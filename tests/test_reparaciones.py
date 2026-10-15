from unittest.mock import MagicMock

import pytest

import reparaciones


DATOS_REPARACION = {
    "vehiculo_id": 1,
    "asunto": "Cambio de filtro",
    "fecha_entrada": "2026-10-15",
    "pieza_id": 3,
    "fecha_salida": None,
    "costo": 250,
    "estado": "Pendiente",
}


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("vehiculo_id", None),
        ("asunto", "   "),
        ("fecha_entrada", ""),
        ("pieza_id", None),
        ("costo", None),
        ("estado", ""),
    ],
)
def test_registrar_reparacion_rechaza_campos_obligatorios_vacios(
    monkeypatch, campo, valor
):
    monkeypatch.setattr(
        reparaciones,
        "conectar_mysql",
        lambda: pytest.fail("No debe conectarse con datos incompletos"),
    )
    datos = {**DATOS_REPARACION, campo: valor}

    with pytest.raises(ValueError):
        reparaciones.registrar_reparacion(**datos)


@pytest.mark.parametrize("recursos", [(0, 1), (1, 0), (0, 0)])
def test_registrar_reparacion_requiere_vehiculo_y_pieza_con_stock(
    monkeypatch, recursos
):
    conexion = MagicMock()
    cursor = conexion.cursor.return_value
    cursor.fetchone.return_value = recursos
    monkeypatch.setattr(reparaciones, "conectar_mysql", lambda: conexion)

    resultado = reparaciones.registrar_reparacion(**DATOS_REPARACION)

    assert resultado is None
    assert cursor.execute.call_count == 1
    conexion.rollback.assert_called_once()
    conexion.commit.assert_not_called()


def test_registrar_reparacion_rechaza_fecha_entrada_posterior(monkeypatch):
    monkeypatch.setattr(
        reparaciones,
        "conectar_mysql",
        lambda: pytest.fail("No debe conectarse con fechas inválidas"),
    )
    datos = {**DATOS_REPARACION, "fecha_entrada": "2026-10-16", "fecha_salida": "2026-10-15"}

    with pytest.raises(ValueError, match="posterior"):
        reparaciones.registrar_reparacion(**datos)


def test_actualizar_reparacion_rechaza_fecha_entrada_posterior(monkeypatch):
    monkeypatch.setattr(
        reparaciones,
        "conectar_mysql",
        lambda: pytest.fail("No debe conectarse con fechas inválidas"),
    )

    with pytest.raises(ValueError, match="posterior"):
        reparaciones.actualizar_reparacion(
            9, 1, "Cambio de filtro", "2026-10-16", "2026-10-15", 3, 250, "Pendiente"
        )


def test_registrar_reparacion_descuenta_la_pieza_en_la_misma_transaccion(monkeypatch):
    conexion = MagicMock()
    cursor = conexion.cursor.return_value
    cursor.fetchone.return_value = (1, 1)
    cursor.lastrowid = 42
    descontar = MagicMock(return_value=True)
    monkeypatch.setattr(reparaciones, "conectar_mysql", lambda: conexion)
    monkeypatch.setattr(reparaciones, "descontar_stock_pieza_en_cursor", descontar)

    resultado = reparaciones.registrar_reparacion(**DATOS_REPARACION)

    assert resultado == 42
    descontar.assert_called_once_with(cursor, 3, 1)
    conexion.commit.assert_called_once()
    conexion.rollback.assert_not_called()


def test_registrar_reparacion_revierte_si_no_hay_stock(monkeypatch):
    conexion = MagicMock()
    cursor = conexion.cursor.return_value
    cursor.fetchone.return_value = (1, 1)
    descontar = MagicMock(return_value=False)
    monkeypatch.setattr(reparaciones, "conectar_mysql", lambda: conexion)
    monkeypatch.setattr(reparaciones, "descontar_stock_pieza_en_cursor", descontar)

    resultado = reparaciones.registrar_reparacion(**DATOS_REPARACION)

    assert resultado is None
    conexion.rollback.assert_called_once()
    conexion.commit.assert_not_called()


def test_actualizar_reparacion_descuenta_nueva_pieza_y_devuelve_anterior(monkeypatch):
    conexion = MagicMock()
    cursor = conexion.cursor.return_value
    cursor.fetchone.return_value = (2,)
    cursor.rowcount = 1
    descontar = MagicMock(return_value=True)
    devolver = MagicMock(return_value=True)
    monkeypatch.setattr(reparaciones, "conectar_mysql", lambda: conexion)
    monkeypatch.setattr(reparaciones, "descontar_stock_pieza_en_cursor", descontar)
    monkeypatch.setattr(reparaciones, "devolver_stock_pieza_en_cursor", devolver)

    resultado = reparaciones.actualizar_reparacion(
        9, 1, "Cambio de filtro", "2026-10-15", None, 3, 250, "Pendiente"
    )

    assert resultado is True
    descontar.assert_called_once_with(cursor, 3, 1)
    devolver.assert_called_once_with(cursor, 2, 1)
    conexion.commit.assert_called_once()
