import os

import mysql.connector

# Configuración de MySQL para XAMPP; se puede sobrescribir con variables de entorno.
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "taller_mecanico")


def conectar_mysql(incluir_base=True):
    """Abre una conexión a MySQL"""
    configuracion = {
        "host": MYSQL_HOST,
        "port": MYSQL_PORT,
        "user": MYSQL_USER,
        "password": MYSQL_PASSWORD,
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
    }
    if incluir_base:
        configuracion["database"] = MYSQL_DATABASE
    return mysql.connector.connect(**configuracion)


def normalizar_texto(texto):
    """Normaliza texto para comparar registros sin diferencias de formato"""
    return " ".join(texto.split()).casefold()
