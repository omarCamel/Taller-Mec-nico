from unittest.mock import Mock

import pytest

import taller_mecanico


@pytest.mark.parametrize(
    "perfil, modulo_permitido",
    [("encargado", "Clientes"), ("mecanico", "Reparaciones")],
)
def test_perfil_operativo_tiene_crud_solo_en_su_modulo(
    perfil, modulo_permitido
):
    app = object.__new__(taller_mecanico.TallerApp)
    app.permisos = taller_mecanico.PERMISOS_POR_PERFIL[perfil]

    for modulo in ("Usuarios", "Clientes", "Vehículos", "Reparaciones", "Piezas"):
        if modulo == modulo_permitido:
            for accion in ("ver", "registrar", "actualizar", "borrar"):
                assert app._tiene_permiso(modulo, accion)
        else:
            for accion in ("ver", "registrar", "actualizar", "borrar"):
                assert not app._tiene_permiso(modulo, accion)


def test_admin_tiene_acceso_total():
    app = object.__new__(taller_mecanico.TallerApp)
    app.permisos = taller_mecanico.PERMISOS_POR_PERFIL["admin"]

    for modulo in ("Usuarios", "Clientes", "Vehículos", "Reparaciones", "Piezas"):
        for accion in ("ver", "registrar", "actualizar", "borrar"):
            assert app._tiene_permiso(modulo, accion)


def test_perfil_desconocido_no_tiene_permisos():
    app = object.__new__(taller_mecanico.TallerApp)
    app.permisos = taller_mecanico.PERMISOS_POR_PERFIL.get("desconocido", {})

    assert not app._tiene_permiso("Clientes", "registrar")
    assert not app._tiene_permiso("Reparaciones", "registrar")


def test_guardia_bloquea_llamada_directa_no_autorizada(monkeypatch):
    app = object.__new__(taller_mecanico.TallerApp)
    app.permisos = taller_mecanico.PERMISOS_POR_PERFIL["encargado"]
    aviso = Mock()
    monkeypatch.setattr(taller_mecanico.messagebox, "showwarning", aviso)

    assert app.registrar_vehiculo() is None
    aviso.assert_called_once()
