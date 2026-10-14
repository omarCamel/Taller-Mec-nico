import mysql.connector

from database import conectar_mysql, normalizar_texto


def pieza_duplicada(nombre, categoria="General", excluir_id=None):
    """Comprueba si ya existe una pieza con el mismo nombre y categoría."""
    nombre_normalizado = normalizar_texto(nombre)
    categoria_normalizada = normalizar_texto(categoria)
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT id, nombre, categoria FROM piezas")
        return any(
            pieza_id != excluir_id
            and normalizar_texto(valor_nombre) == nombre_normalizado
            and normalizar_texto(valor_categoria) == categoria_normalizada
            for pieza_id, valor_nombre, valor_categoria in cursor.fetchall()
        )
    finally:
        cursor.close()
        conexion.close()


def pieza_en_existencia(pieza_id):
    """Devuelve True si la pieza existe y hay stock disponible."""
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT stock FROM piezas WHERE id = %s", (pieza_id,))
        fila = cursor.fetchone()
        return bool(fila) and fila[0] > 0
    finally:
        cursor.close()
        conexion.close()


def registrar_pieza(nombre, descripcion, stock, precio_unitario, categoria="General"):
    """Registra una pieza con validación de nombre único y existencia disponible."""
    if pieza_duplicada(nombre, categoria):
        return None

    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """INSERT INTO piezas (nombre, categoria, stock, precio_unitario, descripcion)
               VALUES (%s, %s, %s, %s, %s)""",
            (
                nombre.strip(),
                categoria.strip() or "General",
                int(stock),
                float(precio_unitario),
                descripcion.strip(),
            ),
        )
        conexion.commit()
        return cursor.lastrowid
    except mysql.connector.IntegrityError:
        conexion.rollback()
        return None
    finally:
        cursor.close()
        conexion.close()


def actualizar_pieza(pieza_id, nombre, descripcion, stock, precio_unitario, categoria="General"):
    """Actualiza una pieza existente."""
    if pieza_duplicada(nombre, categoria, excluir_id=pieza_id):
        return None

    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """UPDATE piezas SET nombre = %s, categoria = %s, stock = %s,
               precio_unitario = %s, descripcion = %s WHERE id = %s""",
            (
                nombre.strip(),
                categoria.strip() or "General",
                int(stock),
                float(precio_unitario),
                descripcion.strip(),
                pieza_id,
            ),
        )
        if cursor.rowcount == 0:
            cursor.execute("SELECT 1 FROM piezas WHERE id = %s", (pieza_id,))
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


def eliminar_pieza(pieza_id):
    """Elimina una pieza por su ID."""
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM piezas WHERE id = %s", (pieza_id,))
        if cursor.rowcount == 0:
            conexion.rollback()
            return False
        conexion.commit()
        return True
    finally:
        cursor.close()
        conexion.close()


def descontar_stock_pieza(pieza_id, cantidad=1):
    """Descuenta existencias de una pieza si hay stock suficiente."""
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "UPDATE piezas SET stock = GREATEST(stock - %s, 0) WHERE id = %s",
            (int(cantidad), pieza_id),
        )
        conexion.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conexion.close()


def devolver_stock_pieza(pieza_id, cantidad=1):
    """Devuelve piezas al inventario tras cancelar o eliminar una reparación."""
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "UPDATE piezas SET stock = stock + %s WHERE id = %s",
            (int(cantidad), pieza_id),
        )
        conexion.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conexion.close()


def cargar_piezas():
    """Carga el inventario de piezas."""
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "SELECT id, nombre, categoria, stock, precio_unitario, descripcion FROM piezas ORDER BY id"
        )
        return [[str(valor) for valor in fila] for fila in cursor.fetchall()]
    finally:
        cursor.close()
        conexion.close()
