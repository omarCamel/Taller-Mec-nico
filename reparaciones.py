from datetime import date

import mysql.connector

from database import conectar_mysql
from piezas import descontar_stock_pieza, devolver_stock_pieza, pieza_en_existencia


ESTADOS_REPARACION = ("Pendiente", "En proceso", "Completada", "Cancelada")


def validar_fechas_reparacion(fecha_entrada, fecha_salida):
    """Valida el formato y orden cronológico de las fechas de una reparación."""
    try:
        entrada = date.fromisoformat(fecha_entrada)
        salida = date.fromisoformat(fecha_salida) if fecha_salida else None
    except (TypeError, ValueError) as error:
        raise ValueError("Las fechas deben tener el formato AAAA-MM-DD.") from error

    if salida is not None and entrada > salida:
        raise ValueError("La fecha de entrada no puede ser posterior a la fecha de salida.")


def registrar_reparacion(
    vehiculo_id,
    asunto,
    fecha_entrada,
    pieza_id,
    fecha_salida=None,
    costo=0.0,
    estado="Pendiente",
):
    """Registra una reparación asociada a un vehículo y a una pieza en existencia."""
    validar_fechas_reparacion(fecha_entrada, fecha_salida)
    if pieza_id not in (None, "") and not pieza_en_existencia(pieza_id):
        return None

    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM vehiculos), "
            "EXISTS(SELECT 1 FROM piezas WHERE stock > 0)"
        )
        hay_vehiculos, hay_piezas_disponibles = cursor.fetchone()
        if not hay_vehiculos or not hay_piezas_disponibles:
            return None

        cursor.execute(
            """INSERT INTO reparaciones
               (vehiculo_id, asunto, fecha_entrada, fecha_salida, pieza_id, costo, estado)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                vehiculo_id,
                asunto.strip(),
                fecha_entrada,
                fecha_salida or None,
                pieza_id if pieza_id not in (None, "") else None,
                costo,
                estado,
            ),
        )
        if pieza_id not in (None, ""):
            descontar_stock_pieza(pieza_id, 1)
        conexion.commit()
        return cursor.lastrowid
    except mysql.connector.IntegrityError:
        conexion.rollback()
        return None
    finally:
        cursor.close()
        conexion.close()


def actualizar_reparacion(
    reparacion_id,
    vehiculo_id,
    asunto,
    fecha_entrada,
    fecha_salida,
    pieza_id,
    costo,
    estado,
):
    """Actualiza los datos de una reparación y ajusa el stock de la pieza usada."""
    validar_fechas_reparacion(fecha_entrada, fecha_salida)
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "SELECT pieza_id FROM reparaciones WHERE id = %s",
            (reparacion_id,),
        )
        reparacion_actual = cursor.fetchone()
        pieza_actual = reparacion_actual[0] if reparacion_actual else None

        if pieza_id not in (None, ""):
            if pieza_actual != pieza_id and not pieza_en_existencia(pieza_id):
                return None

        cursor.execute(
            """UPDATE reparaciones SET vehiculo_id = %s, asunto = %s,
               fecha_entrada = %s, fecha_salida = %s, pieza_id = %s,
               costo = %s, estado = %s WHERE id = %s""",
            (
                vehiculo_id,
                asunto.strip(),
                fecha_entrada,
                fecha_salida or None,
                pieza_id if pieza_id not in (None, "") else None,
                costo,
                estado,
                reparacion_id,
            ),
        )
        if cursor.rowcount == 0:
            cursor.execute("SELECT 1 FROM reparaciones WHERE id = %s", (reparacion_id,))
            if cursor.fetchone() is None:
                conexion.rollback()
                return False

        if pieza_actual and pieza_actual != pieza_id:
            devolver_stock_pieza(pieza_actual, 1)
        if pieza_id not in (None, "") and pieza_actual != pieza_id:
            descontar_stock_pieza(pieza_id, 1)

        conexion.commit()
        return True
    except mysql.connector.IntegrityError:
        conexion.rollback()
        return False
    finally:
        cursor.close()
        conexion.close()


def eliminar_reparacion(reparacion_id):
    """Elimina una reparación y devuelve la pieza al inventario si aplica."""
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT pieza_id FROM reparaciones WHERE id = %s", (reparacion_id,))
        pieza = cursor.fetchone()
        if pieza and pieza[0] is not None:
            devolver_stock_pieza(pieza[0], 1)

        cursor.execute("DELETE FROM reparaciones WHERE id = %s", (reparacion_id,))
        if cursor.rowcount == 0:
            conexion.rollback()
            return False
        conexion.commit()
        return True
    finally:
        cursor.close()
        conexion.close()


def cargar_reparaciones():
    """Carga las reparaciones registradas con su vehículo y pieza asociada."""
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """SELECT id, vehiculo_id, asunto, fecha_entrada, fecha_salida,
                      pieza_id, costo, estado
               FROM reparaciones ORDER BY id"""
        )
        return [
            ["" if valor is None else str(valor) for valor in fila]
            for fila in cursor.fetchall()
        ]
    finally:
        cursor.close()
        conexion.close()