# TuTallerAUnClic Backend

Backend desarrollado con Django y MariaDB.

## Instalación

1. Crear entorno virtual
2. Instalar dependencias:
   pip install -r requirements.txt
3. Configurar base de datos
4. Ejecutar migraciones:
   python manage.py migrate
5. Ejecutar servidor:
   python manage.py runserver

# Para la base de datos:

CREATE DATABASE tutalleraunclic CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

Crear usuario:

CREATE USER 'tutalleraunclic_user'@'localhost' IDENTIFIED BY '123456';

Dar permisos:

GRANT ALL PRIVILEGES ON tutalleraunclic.* TO 'tutalleraunclic_user'@'localhost';
FLUSH PRIVILEGES;