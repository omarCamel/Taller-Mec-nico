import hashlib
import hmac
import secrets

import mysql.connector

from database import conectar_mysql, normalizar_texto


def cargar_usuarios():
    """Carga usuarios registrados"""
    conexion = conectar_mysql()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, nombre, telefono, username, password_hash, perfil FROM usuarios ORDER BY id"
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()


def usuario_duplicado(username, excluir_id=None):
    """Comprueba si el username ya está registrado"""
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        consulta = "SELECT 1 FROM usuarios WHERE username = %s"
        parametros = [username.strip()]
        if excluir_id is not None:
            consulta += " AND id <> %s"
            parametros.append(excluir_id)
        consulta += " LIMIT 1"
        cursor.execute(consulta, parametros)
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conexion.close()


def generar_hash_password(password):
    """Genera un hash salado para almacenar la contraseña"""
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, 260000
    ).hex()
    return f"pbkdf2_sha256${salt.hex()}${password_hash}"


def registrar_usuario(nombre, telefono, username, password, perfil):
    """Registra un usuario y almacena su contraseña con hash salado"""
    username = " ".join(username.split())
    if usuario_duplicado(username):
        return None

    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """INSERT INTO usuarios
               (nombre, telefono, username, password_hash, perfil)
               VALUES (%s, %s, %s, %s, %s)""",
            (nombre.strip(), telefono.strip(), username, generar_hash_password(password), perfil),
        )
        conexion.commit()
        return cursor.lastrowid
    except mysql.connector.IntegrityError:
        conexion.rollback()
        return None
    finally:
        cursor.close()
        conexion.close()


def actualizar_usuario(usuario_id, nombre, telefono, username, perfil, password=""):
    """Actualiza un usuario y cambia la contraseña solo si se proporciona"""
    username = " ".join(username.split())
    if usuario_duplicado(username, excluir_id=usuario_id):
        return None

    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        if password:
            cursor.execute(
                """UPDATE usuarios SET nombre = %s, telefono = %s, username = %s,
                   password_hash = %s, perfil = %s WHERE id = %s""",
                (nombre.strip(), telefono.strip(), username, generar_hash_password(password), perfil, usuario_id),
            )
        else:
            cursor.execute(
                """UPDATE usuarios SET nombre = %s, telefono = %s, username = %s,
                   perfil = %s WHERE id = %s""",
                (nombre.strip(), telefono.strip(), username, perfil, usuario_id),
            )
        if cursor.rowcount == 0:
            cursor.execute("SELECT 1 FROM usuarios WHERE id = %s", (usuario_id,))
            if cursor.fetchone() is None:
                conexion.rollback()
                return False
        conexion.commit()
        return True
    except mysql.connector.IntegrityError:
        conexion.rollback()
        return None
    finally:
        cursor.close()
        conexion.close()


def eliminar_usuario(usuario_id):
    """Elimina un usuario, sin permitir borrar el último administrador"""
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT perfil FROM usuarios WHERE id = %s FOR UPDATE", (usuario_id,))
        usuario = cursor.fetchone()
        if usuario is None:
            return False

        if usuario[0] == "admin":
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE perfil = 'admin'")
            if cursor.fetchone()[0] <= 1:
                return "ultimo_admin"

        cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
        conexion.commit()
        return True
    except mysql.connector.Error:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def autenticar_usuario(username, password):
    """Devuelve el usuario si sus credenciales son válidas"""
    username_normalizado = normalizar_texto(username)
    for usuario in cargar_usuarios():
        if normalizar_texto(usuario.get("username", "")) != username_normalizado:
            continue

        try:
            algoritmo, salt, hash_guardado = usuario["password_hash"].split("$", 2)
            if algoritmo != "pbkdf2_sha256":
                return None
            hash_ingresado = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), bytes.fromhex(salt), 260000
            ).hex()
        except (KeyError, ValueError):
            return None

        if hmac.compare_digest(hash_ingresado, hash_guardado):
            return usuario
        return None
    return None
