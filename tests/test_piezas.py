from unittest.mock import MagicMock, Mock

import piezas
import taller_mecanico


def test_buscar_pieza_por_id_devuelve_datos_en_formato_de_inventario(monkeypatch):
    conexion = MagicMock()
    cursor = conexion.cursor.return_value
    cursor.fetchone.return_value = (7, "Filtro", "Motor", 4, 12.5, "Descripción")
    monkeypatch.setattr(piezas, "conectar_mysql", lambda: conexion)

    resultado = piezas.buscar_pieza_por_id(7)

    assert resultado == ["7", "Filtro", "Motor", "4", "12.5", "Descripción"]
    cursor.execute.assert_called_once_with(
        """SELECT id, nombre, categoria, stock, precio_unitario, descripcion
               FROM piezas WHERE id = %s""",
        (7,),
    )
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()


def test_buscar_pieza_por_id_devuelve_none_si_no_existe(monkeypatch):
    conexion = MagicMock()
    cursor = conexion.cursor.return_value
    cursor.fetchone.return_value = None
    monkeypatch.setattr(piezas, "conectar_mysql", lambda: conexion)

    assert piezas.buscar_pieza_por_id(99) is None
    cursor.close.assert_called_once()
    conexion.close.assert_called_once()


def test_buscar_piezas_numero_busca_por_id_exacto(monkeypatch):
    app = object.__new__(taller_mecanico.TallerApp)
    app.txt_buscar_pieza = Mock()
    app.txt_buscar_pieza.get.return_value = "7"
    app.mostrar_datos_pieza = Mock()
    app.limpiar_campos_pieza = Mock()
    pieza = ["7", "Filtro", "Motor", "4", "12.5", "Descripción"]
    buscar = Mock(return_value=pieza)
    cargar = Mock(side_effect=AssertionError("No debe cargar todo el inventario"))
    monkeypatch.setattr(taller_mecanico, "buscar_pieza_por_id", buscar)
    monkeypatch.setattr(taller_mecanico, "cargar_piezas", cargar)

    app.buscar_piezas()

    buscar.assert_called_once_with(7)
    cargar.assert_not_called()
    app.mostrar_datos_pieza.assert_called_once_with(pieza)
    app.limpiar_campos_pieza.assert_not_called()


def test_buscar_piezas_numero_limpia_formulario_si_id_no_existe(monkeypatch):
    app = object.__new__(taller_mecanico.TallerApp)
    app.txt_buscar_pieza = Mock()
    app.txt_buscar_pieza.get.return_value = "99"
    app.mostrar_datos_pieza = Mock()
    app.limpiar_campos_pieza = Mock()
    buscar = Mock(return_value=None)
    aviso = Mock()
    monkeypatch.setattr(taller_mecanico, "buscar_pieza_por_id", buscar)
    monkeypatch.setattr(taller_mecanico.messagebox, "showinfo", aviso)

    app.buscar_piezas()

    buscar.assert_called_once_with(99)
    app.limpiar_campos_pieza.assert_called_once()
    app.mostrar_datos_pieza.assert_not_called()
    aviso.assert_called_once()
