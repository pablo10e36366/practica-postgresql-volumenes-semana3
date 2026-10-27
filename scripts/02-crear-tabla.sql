CREATE TABLE customer (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fullname VARCHAR(120) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('activo', 'inactivo'))
);
