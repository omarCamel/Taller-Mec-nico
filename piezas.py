import mysql.connector

from database import conectar_mysql, normalizar_texto


def _normalizar_nombre(nombre):
    return " ".join(nombre.split())


def _normalizar_categoria(categoria):
    return " ".join(categoria.split()) or "General"


def _validar_valores_pieza(stock, precio_unitario):
    stock = int(stock)
    precio_unitario = float(precio_unitario)
    if stock < 0:
        raise ValueError("El stock no puede ser negativo.")
    if precio_unitario < 0:
        raise ValueError("El precio unitario no puede ser negativo.")
    return stock, precio_unitario


def _validar_cantidad(cantidad):
    cantidad = int(cantidad)
    if cantidad < 0:
        raise ValueError("La cantidad no puede ser negativa.")
    return cantidad


def pieza_duplicada(nombre, categoria="General", excluir_id=None):
    """Comprueba si ya existe una pieza con el mismo nombre y categoría."""
    nombre_normalizado = normalizar_texto(nombre)
    categoria_normalizada = normalizar_texto(_normalizar_categoria(categoria))
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
    stock, precio_unitario = _validar_valores_pieza(stock, precio_unitario)
    nombre = _normalizar_nombre(nombre)
    categoria = _normalizar_categoria(categoria)
    if pieza_duplicada(nombre, categoria):
        return None

    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """INSERT INTO piezas (nombre, categoria, stock, precio_unitario, descripcion)
               VALUES (%s, %s, %s, %s, %s)""",
            (
                nombre,
                categoria,
                stock,
                precio_unitario,
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
    stock, precio_unitario = _validar_valores_pieza(stock, precio_unitario)
    nombre = _normalizar_nombre(nombre)
    categoria = _normalizar_categoria(categoria)
    if pieza_duplicada(nombre, categoria, excluir_id=pieza_id):
        return None

    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """UPDATE piezas SET nombre = %s, categoria = %s, stock = %s,
               precio_unitario = %s, descripcion = %s WHERE id = %s""",
            (
                nombre,
                categoria,
                stock,
                precio_unitario,
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
        return None
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
    cantidad = _validar_cantidad(cantidad)
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        resultado = descontar_stock_pieza_en_cursor(cursor, pieza_id, cantidad)
        conexion.commit()
        return resultado
    finally:
        cursor.close()
        conexion.close()


def descontar_stock_pieza_en_cursor(cursor, pieza_id, cantidad=1):
    """Descuenta existencias dentro de la transacción del cursor recibido."""
    cantidad = _validar_cantidad(cantidad)
    cursor.execute(
        """UPDATE piezas SET stock = stock - %s
           WHERE id = %s AND stock >= %s""",
        (cantidad, pieza_id, cantidad),
    )
    return cursor.rowcount > 0


def devolver_stock_pieza(pieza_id, cantidad=1):
    """Devuelve piezas al inventario tras cancelar o eliminar una reparación."""
    cantidad = _validar_cantidad(cantidad)
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    try:
        resultado = devolver_stock_pieza_en_cursor(cursor, pieza_id, cantidad)
        conexion.commit()
        return resultado
    finally:
        cursor.close()
        conexion.close()


def devolver_stock_pieza_en_cursor(cursor, pieza_id, cantidad=1):
    """Devuelve existencias dentro de la transacción del cursor recibido."""
    cantidad = _validar_cantidad(cantidad)
    cursor.execute(
        "UPDATE piezas SET stock = stock + %s WHERE id = %s",
        (cantidad, pieza_id),
    )
    return cursor.rowcount > 0


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
