SELECT datname FROM pg_database WHERE datname = 'test';
SELECT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'test') AS test_disponible;
