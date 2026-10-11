import mysql.connector

from database import conectar_mysql, normalizar_texto


def matricula_duplicada(matricula, excluir_id=None):
    """Comprueba si ya existe un vehículo con la misma matrícula"""
    matricula_normalizada = normalizar_texto(matricula)
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT id, matricula FROM vehiculos")
        return any(
            vehiculo_id != excluir_id and normalizar_texto(valor) == matricula_normalizada
            for vehiculo_id, valor in cursor.fetchall()
        )
    finally:
        cursor.close()
        conexion.close()


def registrar_vehiculo(cliente_id, matricula, marca, modelo, año, color):
    """Registra un vehículo asociado a un cliente en MySQL"""
    if matricula_duplicada(matricula):
        return False
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """INSERT INTO vehiculos (cliente_id, matricula, marca, modelo, anio, color)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (cliente_id, matricula.strip(), marca.strip(), modelo.strip(), int(año), color.strip()),
        )
        conexion.commit()
        return True
    except mysql.connector.IntegrityError:
        conexion.rollback()
        return False
    finally:
        cursor.close()
        conexion.close()


def actualizar_vehiculo(vehiculo_id, cliente_id, matricula, marca, modelo, año, color):
    """Actualiza los datos de un vehículo"""
    if matricula_duplicada(matricula, excluir_id=vehiculo_id):
        return None
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """UPDATE vehiculos SET cliente_id = %s, matricula = %s, marca = %s,
               modelo = %s, anio = %s, color = %s WHERE id = %s""",
            (cliente_id, matricula.strip(), marca.strip(), modelo.strip(), int(año), color.strip(), vehiculo_id),
        )
        if cursor.rowcount == 0:
            cursor.execute("SELECT 1 FROM vehiculos WHERE id = %s", (vehiculo_id,))
            if cursor.fetchone() is None:
                conexion.rollback()
                return False
        conexion.commit()
        return True
    except mysql.connector.IntegrityError:
        conexion.rollback()
        return False
    finally:
        cursor.close()
        conexion.close()


def eliminar_vehiculo(vehiculo_id):
    """Elimina un vehículo por su ID"""
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM vehiculos WHERE id = %s", (vehiculo_id,))
        if cursor.rowcount == 0:
            conexion.rollback()
            return False
        conexion.commit()
        return True
    finally:
        cursor.close()
        conexion.close()


def cargar_vehiculos():
    """Carga vehículos registrados en MySQL"""
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "SELECT id, cliente_id, matricula, marca, modelo, anio, color FROM vehiculos ORDER BY id"
        )
        return [[str(valor) for valor in fila] for fila in cursor.fetchall()]
    finally:
        cursor.close()
        conexion.close()
