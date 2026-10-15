from datetime import date
from math import isfinite

import mysql.connector

from database import conectar_mysql
from piezas import descontar_stock_pieza_en_cursor, devolver_stock_pieza_en_cursor


ESTADOS_REPARACION = ("Pendiente", "En proceso", "Completada", "Cancelada")


def _validar_datos_reparacion(
    vehiculo_id, asunto, fecha_entrada, pieza_id, cantidad_pieza, costo, estado
):
    if vehiculo_id in (None, ""):
        raise ValueError("El vehículo es obligatorio.")
    if not asunto or not asunto.strip():
        raise ValueError("El asunto es obligatorio.")
    if fecha_entrada in (None, ""):
        raise ValueError("La fecha de entrada es obligatoria.")
    if pieza_id in (None, ""):
        raise ValueError("Debe seleccionar una pieza.")
    if cantidad_pieza in (None, ""):
        raise ValueError("La cantidad de piezas es obligatoria.")
    if costo in (None, ""):
        raise ValueError("El costo es obligatorio.")
    if estado not in ESTADOS_REPARACION:
        raise ValueError("Seleccione un estado válido para la reparación.")

    vehiculo_id = int(vehiculo_id)
    pieza_id = int(pieza_id)
    cantidad_original = cantidad_pieza
    try:
        cantidad_pieza = int(cantidad_pieza)
    except (TypeError, ValueError) as error:
        raise ValueError("La cantidad de piezas debe ser un entero positivo.") from error
    if cantidad_pieza < 1 or (
        not isinstance(cantidad_original, str) and cantidad_original != cantidad_pieza
    ):
        raise ValueError("La cantidad de piezas debe ser un entero positivo.")
    costo = float(costo)
    if not isfinite(costo) or costo < 0:
        raise ValueError("El costo debe ser un número no negativo.")
    return vehiculo_id, asunto.strip(), pieza_id, cantidad_pieza, costo, estado


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
    cantidad_pieza=1,
):
    """Registra una reparación asociada a un vehículo y a una pieza en existencia."""
    vehiculo_id, asunto, pieza_id, cantidad_pieza, costo, estado = _validar_datos_reparacion(
        vehiculo_id, asunto, fecha_entrada, pieza_id, cantidad_pieza, costo, estado
    )
    validar_fechas_reparacion(fecha_entrada, fecha_salida)

    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM vehiculos WHERE id = %s), "
            "EXISTS(SELECT 1 FROM piezas WHERE id = %s AND stock >= %s)",
            (vehiculo_id, pieza_id, cantidad_pieza),
        )
        hay_vehiculos, hay_piezas_disponibles = cursor.fetchone()
        if not hay_vehiculos or not hay_piezas_disponibles:
            conexion.rollback()
            return None

        cursor.execute(
            """INSERT INTO reparaciones
               (vehiculo_id, asunto, fecha_entrada, fecha_salida, pieza_id,
                cantidad_pieza, costo, estado)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                vehiculo_id,
                asunto.strip(),
                fecha_entrada,
                fecha_salida or None,
                pieza_id,
                cantidad_pieza,
                costo,
                estado,
            ),
        )
        if not descontar_stock_pieza_en_cursor(cursor, pieza_id, cantidad_pieza):
            conexion.rollback()
            return None
        conexion.commit()
        return cursor.lastrowid
    except mysql.connector.IntegrityError:
        conexion.rollback()
        return None
    except mysql.connector.Error:
        conexion.rollback()
        raise
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
    cantidad_pieza=1,
):
    """Actualiza la reparación y ajusta el inventario según la cantidad utilizada."""
    if reparacion_id in (None, ""):
        raise ValueError("La reparación es obligatoria.")
    reparacion_id = int(reparacion_id)
    vehiculo_id, asunto, pieza_id, cantidad_pieza, costo, estado = _validar_datos_reparacion(
        vehiculo_id, asunto, fecha_entrada, pieza_id, cantidad_pieza, costo, estado
    )
    validar_fechas_reparacion(fecha_entrada, fecha_salida)
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "SELECT pieza_id, cantidad_pieza FROM reparaciones WHERE id = %s",
            (reparacion_id,),
        )
        reparacion_actual = cursor.fetchone()
        pieza_actual = reparacion_actual[0] if reparacion_actual else None
        cantidad_actual = int(reparacion_actual[1]) if reparacion_actual else 0

        cursor.execute(
            """UPDATE reparaciones SET vehiculo_id = %s, asunto = %s,
               fecha_entrada = %s, fecha_salida = %s, pieza_id = %s, cantidad_pieza = %s,
               costo = %s, estado = %s WHERE id = %s""",
            (
                vehiculo_id,
                asunto.strip(),
                fecha_entrada,
                fecha_salida or None,
                pieza_id,
                cantidad_pieza,
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

        if pieza_actual == pieza_id:
            diferencia_cantidad = cantidad_pieza - cantidad_actual
            if diferencia_cantidad > 0 and not descontar_stock_pieza_en_cursor(
                cursor, pieza_id, diferencia_cantidad
            ):
                conexion.rollback()
                return None
            if diferencia_cantidad < 0:
                devolver_stock_pieza_en_cursor(cursor, pieza_actual, -diferencia_cantidad)
        else:
            if not descontar_stock_pieza_en_cursor(cursor, pieza_id, cantidad_pieza):
                conexion.rollback()
                return None
            if pieza_actual is not None:
                devolver_stock_pieza_en_cursor(cursor, pieza_actual, cantidad_actual)

        conexion.commit()
        return True
    except mysql.connector.IntegrityError:
        conexion.rollback()
        return False
    except mysql.connector.Error:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def eliminar_reparacion(reparacion_id):
    """Elimina una reparación y devuelve la pieza al inventario si aplica."""
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "SELECT pieza_id, cantidad_pieza FROM reparaciones WHERE id = %s",
            (reparacion_id,),
        )
        pieza = cursor.fetchone()
        if pieza and pieza[0] is not None:
            devolver_stock_pieza_en_cursor(cursor, pieza[0], int(pieza[1]))

        cursor.execute("DELETE FROM reparaciones WHERE id = %s", (reparacion_id,))
        if cursor.rowcount == 0:
            conexion.rollback()
            return False
        conexion.commit()
        return True
    except mysql.connector.Error:
        conexion.rollback()
        raise
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
                      pieza_id, cantidad_pieza, costo, estado
               FROM reparaciones ORDER BY id"""
        )
        return [
            ["" if valor is None else str(valor) for valor in fila]
            for fila in cursor.fetchall()
        ]
    finally:
        cursor.close()
        conexion.close()