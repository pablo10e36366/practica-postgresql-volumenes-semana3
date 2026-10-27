"""Ejecuta pruebas reales; aborta si los recursos solicitados ya existen.

Requiere Python 3, Docker Desktop iniciado y, para capturas opcionales, Pillow.
Nunca elimina volúmenes ni recursos ajenos. Ver README para reproducir.
"""
import argparse
import ctypes
from ctypes import wintypes
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent.parent
EVID = BASE / 'evidencias'
LOCAL = BASE / '.local'
LABEL = 'edu.practica=postgresql-volumenes-semana3-pablo-ortega'
started = dt.datetime.now(dt.timezone.utc)
events = []
result = {'inicio_utc': started.isoformat(), 'estado': 'en_proceso', 'pruebas': {}}
current = []
hwnd = None

def raw(args, data=None):
    return subprocess.run(args, cwd=BASE, input=data, text=True, encoding='utf-8', errors='replace', capture_output=True, timeout=240)

def configure_console():
    global hwnd
    if os.name != 'nt': return
    kernel = ctypes.windll.kernel32
    user = ctypes.windll.user32
    user.SetProcessDPIAware()
    user.SetWindowPos.argtypes=[wintypes.HWND,wintypes.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,wintypes.UINT]
    kernel.GetConsoleWindow.restype = wintypes.HWND
    hwnd = kernel.GetConsoleWindow()
    if not hwnd: return
    kernel.SetConsoleOutputCP(65001)
    kernel.SetConsoleTitleW('Practica PostgreSQL | Ejecucion real | Pablo Ortega')
    class COORD(ctypes.Structure):
        _fields_ = [('X', ctypes.c_short), ('Y', ctypes.c_short)]
    class FONT(ctypes.Structure):
        _fields_ = [('cbSize',wintypes.ULONG),('nFont',wintypes.DWORD),('dwFontSize',COORD),('FontFamily',wintypes.UINT),('FontWeight',wintypes.UINT),('FaceName',wintypes.WCHAR*32)]
    kernel.GetStdHandle.restype = wintypes.HANDLE
    out = kernel.GetStdHandle(-11)
    font=FONT();font.cbSize=ctypes.sizeof(font);font.dwFontSize=COORD(0,16);font.FontFamily=54;font.FontWeight=400;font.FaceName='Consolas'
    kernel.SetCurrentConsoleFontEx(out, False, ctypes.byref(font))
    user.ShowWindow(hwnd, 9)
    user.SetWindowPos(hwnd, wintypes.HWND(-1), 30, 40, 790, 880, 0x0040)
    user.SetForegroundWindow(hwnd)

def run(args, allowed=(0,), data=None):
    command = subprocess.list2cmdline(args)
    print('\n> '+command, flush=True)
    proc = raw(args, data)
    output = proc.stdout + proc.stderr
    if output: print(output.rstrip(), flush=True)
    rec={'comando':command,'stdin':data,'stdout':proc.stdout,'stderr':proc.stderr,'codigo':proc.returncode,'utc':dt.datetime.now(dt.timezone.utc).isoformat()}
    current.append(rec);events.append(rec)
    (LOCAL/'progreso.json').write_text(json.dumps({'ultimo_comando':command,'eventos':len(events)},ensure_ascii=False),encoding='utf-8')
    if proc.returncode not in allowed: raise RuntimeError(f'Fallo del comando: {command} (codigo {proc.returncode})')
    return proc.stdout.strip()

def begin(number,title):
    global current
    current=[]
    if hwnd: os.system('cls')
    print(f'PRACTICA 3 | EVIDENCIA {number}\n{title}\n'+'='*70,flush=True)

def finish(name):
    text='\n\n'.join('> '+x['comando']+'\n'+('SQL enviado por stdin:\n'+x['stdin']+'\n' if x.get('stdin') else '')+x['stdout']+x['stderr']+'\n[codigo de salida: '+str(x['codigo'])+']' for x in current)
    (EVID/(name+'.txt')).write_text(text+'\n',encoding='utf-8')
    if not hwnd: return
    try:
        from PIL import ImageGrab
        rect=wintypes.RECT()
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        ctypes.windll.user32.GetClientRect(hwnd,ctypes.byref(rect))
        origin=wintypes.POINT(0,0)
        ctypes.windll.user32.ClientToScreen(hwnd,ctypes.byref(origin))
        time.sleep(.7)
        picture=ImageGrab.grab(bbox=(origin.x,origin.y,origin.x+rect.right,origin.y+rect.bottom))
        # El docente exige figuras de hasta 800 px. Solo se ajusta el tamaño;
        # no se modifican los comandos ni las salidas capturadas.
        if picture.width > 800:
            from PIL import Image
            picture=picture.resize((800,round(picture.height*800/picture.width)),Image.Resampling.LANCZOS)
        picture.save(EVID/(name+'.png'))
    except Exception as exc:
        (LOCAL/'capturas_error.txt').open('a',encoding='utf-8').write(name+': '+str(exc)+'\n')

def sql(container, db, text):
    return run(['docker','exec',container,'psql','-X','-v','ON_ERROR_STOP=1','-P','pager=off','-U','postgres','-d',db,'-c',text])

def sqlfile(container,db,name):
    # El archivo SQL se transmite por stdin, sin modificar el contenedor.
    data=(BASE/'scripts'/name).read_text(encoding='utf-8')
    print('\nSQL enviado desde scripts/'+name+':\n'+data,flush=True)
    return run(['docker','exec','-i',container,'psql','-X','-v','ON_ERROR_STOP=1','-P','pager=off','-U','postgres','-d',db],data=data)

def wait_ready(container):
    command=['docker','exec',container,'pg_isready','-h','127.0.0.1','-U','postgres']
    for _ in range(75):
        if raw(command).returncode==0:
            run(command);return
        time.sleep(1)
    raise RuntimeError('PostgreSQL no quedo listo: '+container)

def create(container,port,volume=False):
    args=['docker','run','-d','--name',container,'--label',LABEL,'--env-file','.env.local','-p',f'127.0.0.1:{port}:5432']
    if volume: args.extend(['--mount','type=volume,source=pgdata,target=/var/lib/postgresql/data'])
    args.append('postgres:16')
    return run(args)

def owned_remove(container):
    label=raw(['docker','inspect','--format','{{index .Config.Labels "edu.practica"}}',container])
    if label.stdout.strip()!=LABEL.split('=',1)[1]:raise RuntimeError('No se elimina un recurso que no pertenece a esta practica.')
    run(['docker','stop',container]);run(['docker','rm',container])

def mount(container):
    proc=raw(['docker','inspect','--format','{{json .Mounts}}',container])
    if proc.returncode:raise RuntimeError(proc.stderr)
    return next(m for m in json.loads(proc.stdout) if m['Destination']=='/var/lib/postgresql/data')

def cluster(container):
    return raw(['docker','exec',container,'psql','-X','-At','-U','postgres','-d','postgres','-c','SELECT system_identifier FROM pg_control_system();']).stdout.strip()

def clients(container):
    p=raw(['docker','exec',container,'psql','-X','-At','-F','|','-U','postgres','-d','test','-c','SELECT id, fullname, status FROM customer ORDER BY id;'])
    if p.returncode:raise RuntimeError(p.stderr)
    return p.stdout.strip()

def main():
    configure_console()
    EVID.mkdir(exist_ok=True);LOCAL.mkdir(exist_ok=True)
    os.chdir(BASE)
    before=json.loads(raw(['docker','ps','-aq','--no-trunc']).stdout and json.dumps(raw(['docker','ps','-aq','--no-trunc']).stdout.split()) or '[]')
    (LOCAL/'contenedores_previos.json').write_text(json.dumps(before),encoding='utf-8')
    for name in ['server_db1','server_db2']:
        if raw(['docker','container','inspect',name]).returncode==0:raise RuntimeError('Nombre ocupado; no se modifica: '+name)
    volume_existing=raw(['docker','volume','inspect','pgdata']).returncode==0
    if volume_existing:
        check=raw(['docker','volume','inspect','pgdata','--format','{{index .Labels "edu.practica"}}'])
        if '--reuse-owned-empty-volume' not in sys.argv or check.stdout.strip()!=LABEL.split('=',1)[1]:
            raise RuntimeError('Volumen pgdata ya existe; no se modifica.')
    result['pgdata_existia_al_inicio']=volume_existing
    ports=[]
    for port in range(5433,5534):
        with socket.socket() as sock:
            try:sock.bind(('127.0.0.1',port))
            except OSError:continue
            ports.append(port)
        if len(ports)==2:break
    if len(ports)!=2:raise RuntimeError('No hay dos puertos locales disponibles.')
    result['puertos']={'server_db1':ports[0],'server_db2':ports[1]}
    if not (BASE/'.env.local').exists():
        (BASE/'.env.local').write_text('POSTGRES_PASSWORD='+secrets.token_urlsafe(24)+'\n',encoding='ascii')
    begin('01','Docker Desktop y Ubuntu WSL 2 funcionando')
    run(['docker','version','--format','Cliente={{.Client.Version}} Servidor={{.Server.Version}}'])
    run(['docker','info','--format','Motor={{.OSType}} / {{.OperatingSystem}}'])
    run(['wsl','-d','Ubuntu','--','head','-n','3','/etc/os-release'])
    run(['wsl','-d','Ubuntu','--','uname','-r'])
    finish('01-docker-ubuntu')
    if raw(['docker','image','inspect','postgres:16']).returncode!=0:
        run(['docker','pull','postgres:16'])
    begin('02','Imagen oficial PostgreSQL 16 y ruta de datos')
    result['imagen_digest']=run(['docker','image','inspect','postgres:16','--format','{{index .RepoDigests 0}}'])
    run(['docker','image','inspect','postgres:16','--format','{{json .Config.Volumes}}'])
    finish('02-imagen-postgres')
    begin('03','Crear server_db1 sin reutilizar un volumen anterior')
    result['db1_id_antes']=create('server_db1',ports[0]);wait_ready('server_db1')
    result['db1_montaje_antes']=mount('server_db1');result['db1_cluster_antes']=cluster('server_db1')
    run(['docker','inspect','server_db1','--format','{{range .Mounts}}{{println .Type .Name .Destination}}{{end}}'])
    finish('03-server-db1')
    begin('04','Crear la base test y la tabla customer en server_db1')
    sqlfile('server_db1','postgres','01-crear-base.sql');sqlfile('server_db1','test','02-crear-tabla.sql')
    sql('server_db1','test',r'\d customer')
    finish('04-base-tabla-db1')
    begin('05','Insertar clientes y comprobarlos con SELECT')
    sqlfile('server_db1','test','03-insertar-clientes.sql');sqlfile('server_db1','test','04-consultar-clientes.sql')
    result['db1_clientes_antes']=clients('server_db1')
    finish('05-registros-db1')
    begin('06','Eliminar y recrear solo server_db1, con almacenamiento nuevo')
    owned_remove('server_db1')
    result['db1_id_despues']=create('server_db1',ports[0]);wait_ready('server_db1')
    result['db1_montaje_despues']=mount('server_db1');result['db1_cluster_despues']=cluster('server_db1')
    finish('06-recrear-db1')
    begin('07','El contenedor nuevo no recupera la base test')
    sqlfile('server_db1','postgres','05-comprobar-base.sql')
    run(['docker','exec','server_db1','psql','-X','-U','postgres','-d','test','-c','SELECT 1;'],allowed=(2,))
    old=result['db1_montaje_antes']['Name']
    run(['docker','volume','inspect',old,'--format','Volumen anterior conservado: {{.Name}}'])
    run(['docker','inspect','server_db1','--format','Volumen del contenedor nuevo: {{range .Mounts}}{{.Name}}{{end}}'])
    exists=raw(['docker','exec','server_db1','psql','-X','-At','-U','postgres','-d','postgres','-c',"SELECT EXISTS (SELECT 1 FROM pg_database WHERE datname='test');"]).stdout.strip()
    assert exists=='f'
    assert old!=result['db1_montaje_despues']['Name']
    assert result['db1_cluster_antes']!=result['db1_cluster_despues']
    result['pruebas']['db1_no_recupera_test']=True
    result['pruebas']['db1_volumen_anonimo_distinto']=True
    result['pruebas']['volumen_anonimo_anterior_conservado']=True
    finish('07-test-no-disponible')
    begin('08','Crear el volumen con nombre pgdata')
    run(['docker','volume','create','--label',LABEL,'pgdata'])
    run(['docker','volume','inspect','pgdata','--format','Nombre={{.Name}} Controlador={{.Driver}}'])
    finish('08-volumen-pgdata')
    begin('09','Crear server_db2 con pgdata en /var/lib/postgresql/data')
    result['db2_id_antes']=create('server_db2',ports[1],True);wait_ready('server_db2')
    result['db2_montaje_antes']=mount('server_db2');result['db2_cluster_antes']=cluster('server_db2')
    run(['docker','inspect','server_db2','--format','{{range .Mounts}}{{println .Type .Name .Destination}}{{end}}'])
    finish('09-server-db2')
    begin('10','Crear la base test y tabla customer en server_db2')
    sqlfile('server_db2','postgres','01-crear-base.sql');sqlfile('server_db2','test','02-crear-tabla.sql')
    sql('server_db2','test',r'\d customer')
    finish('10-base-tabla-db2')
    begin('11','Guardar y consultar registros en el volumen persistente')
    sqlfile('server_db2','test','03-insertar-clientes.sql');sqlfile('server_db2','test','04-consultar-clientes.sql')
    result['db2_clientes_antes']=clients('server_db2')
    finish('11-registros-db2')
    begin('12','Eliminar y recrear server_db2 reutilizando pgdata')
    owned_remove('server_db2')
    run(['docker','volume','inspect','pgdata','--format','El volumen sigue disponible: {{.Name}}'])
    result['db2_id_despues']=create('server_db2',ports[1],True);wait_ready('server_db2')
    result['db2_montaje_despues']=mount('server_db2');result['db2_cluster_despues']=cluster('server_db2')
    finish('12-recrear-db2')
    begin('13','Consulta final: base, tabla y registros persisten sin recrear el esquema')
    sqlfile('server_db2','postgres','05-comprobar-base.sql');sqlfile('server_db2','test','04-consultar-clientes.sql')
    result['db2_clientes_despues']=clients('server_db2')
    assert result['db2_clientes_despues']==result['db2_clientes_antes']
    assert len(result['db2_clientes_despues'].splitlines())==2
    assert result['db2_cluster_antes']==result['db2_cluster_despues']
    assert result['db2_montaje_despues']['Name']=='pgdata'
    assert result['db2_id_antes']!=result['db2_id_despues']
    result['pruebas']['db2_dos_registros_persisten']=True
    result['pruebas']['db2_mismo_cluster_y_volumen']=True
    result['pruebas']['db2_contenedor_recreado']=True
    finish('13-persistencia-verificada')
    begin('14','Estado final: ambos contenedores y el volumen pgdata')
    run(['docker','ps','--filter','label='+LABEL,'--format','table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'])
    run(['docker','volume','ls','--filter','label='+LABEL,'--format','table {{.Name}}\t{{.Driver}}'])
    run(['docker','inspect','server_db2','--format','{{range .Mounts}}{{println .Name "->" .Destination}}{{end}}'])
    after=raw(['docker','ps','-aq','--no-trunc']).stdout.split()
    assert set(before).issubset(after)
    result['pruebas']['contenedores_previos_conservados']=True
    finish('14-estado-final')
    result['estado']='completado'

if __name__=='__main__':
    try: main()
    except Exception as exc:
        result['estado']='error';result['error']=str(exc)
        print('\nERROR: '+str(exc),flush=True)
    finally:
        ended=dt.datetime.now(dt.timezone.utc)
        result['fin_utc']=ended.isoformat();result['duracion_segundos']=round((ended-started).total_seconds(),2)
        EVID.mkdir(exist_ok=True)
        (EVID/'resultados.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        (EVID/'comandos-ejecutados.json').write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding='utf-8')
        print('\nEstado final: '+result['estado'],flush=True)
        if hwnd:time.sleep(2)
    sys.exit(0 if result['estado']=='completado' else 1)
