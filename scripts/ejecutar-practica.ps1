# Ejecutar en PowerShell desde la carpeta del proyecto.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
python "$PSScriptRoot\ejecutar-practica.py"
if ($LASTEXITCODE -ne 0) { throw 'La práctica se detuvo. Revise evidencias/resultados.json; no se borraron recursos ajenos.' }
