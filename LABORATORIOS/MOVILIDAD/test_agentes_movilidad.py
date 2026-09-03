"""Pruebas para agentes_movilidad.py.
"""

from __future__ import annotations

import inspect

import pandas as pd
import pytest

from agentes_movilidad import (
    actualizar_estado,
    crear_estado_inicial,
    decidir_reactivo_modelo,
    decidir_reactivo_simple,
    procesar_secuencia,
)


def _percepcion(hora: int, presion: float, **overrides) -> dict:
    """Construye una percepción mínima válida con la presión indicada."""
    capacidad_x = overrides.pop("capacidad_x", 10)
    demanda_x = overrides.pop("demanda_x", round(presion * capacidad_x))
    base = {
        "zona_id": 161,
        "zona": "Zona de prueba",
        "hora": hora,
        "taxis_x": 10,
        "demanda_total": demanda_x + 5,
        "tasa_otras_simulada": 0.3,
        "viajes_otras": 5,
        "demanda_x": demanda_x,
        "capacidad_x": capacidad_x,
        "viajes_atendibles_x": min(demanda_x, capacidad_x),
        "demanda_no_cubierta_x": max(demanda_x - capacidad_x, 0),
        "presion": presion,
    }
    base.update(overrides)
    return base


# Caso 1: presión baja -> ambos agentes devuelven NO_REFORZAR.
def test_presion_baja_ambos_no_refuerzan():
    percepcion = _percepcion(hora=8, presion=0.4)

    accion_simple, _ = decidir_reactivo_simple(percepcion)

    estado = actualizar_estado(crear_estado_inicial(), percepcion)
    accion_modelo, _ = decidir_reactivo_modelo(estado)

    assert accion_simple == "NO_REFORZAR"
    assert accion_modelo == "NO_REFORZAR"


# Caso 2: primera hora con presión alta -> simple recomienda, modelo todavía no.
def test_primera_hora_presion_alta_difieren():
    percepcion = _percepcion(hora=8, presion=0.9)

    accion_simple, _ = decidir_reactivo_simple(percepcion)

    estado = actualizar_estado(crear_estado_inicial(), percepcion)
    accion_modelo, _ = decidir_reactivo_modelo(estado)

    assert accion_simple == "RECOMENDAR_REFUERZO"
    assert accion_modelo == "NO_REFORZAR"
    assert estado["racha_presion_alta"] == 1


# Caso 3: segunda hora consecutiva con presión alta -> ambos recomiendan.
def test_segunda_hora_consecutiva_ambos_refuerzan():
    percepcion_h1 = _percepcion(hora=8, presion=0.9)
    percepcion_h2 = _percepcion(hora=9, presion=0.95)

    estado = crear_estado_inicial()
    estado = actualizar_estado(estado, percepcion_h1)
    estado = actualizar_estado(estado, percepcion_h2)

    accion_simple, _ = decidir_reactivo_simple(percepcion_h2)
    accion_modelo, _ = decidir_reactivo_modelo(estado)

    assert accion_simple == "RECOMENDAR_REFUERZO"
    assert accion_modelo == "RECOMENDAR_REFUERZO"
    assert estado["racha_presion_alta"] == 2


# Caso adicional: percepción inválida -> ambos se abstienen.
def test_percepcion_invalida_ambos_se_abstienen():
    percepcion_invalida = _percepcion(hora=8, presion=0.9)
    percepcion_invalida["capacidad_x"] = None  # capacidad desconocida

    accion_simple, _ = decidir_reactivo_simple(percepcion_invalida)

    estado = actualizar_estado(crear_estado_inicial(), percepcion_invalida)
    accion_modelo, _ = decidir_reactivo_modelo(estado)

    assert accion_simple == "ABSTENERSE"
    assert accion_modelo == "ABSTENERSE"
    assert estado["racha_presion_alta"] == 0


# Prueba decisiva: dos historias distintas que terminan en la misma percepción.
def test_dependencia_historica_misma_percepcion_distinta_historia():
    percepcion_final = _percepcion(hora=10, presion=0.9)

    # Historia A: una sola hora previa de presión alta -> racha llega a 2.
    estado_a = crear_estado_inicial()
    estado_a = actualizar_estado(estado_a, _percepcion(hora=9, presion=0.9))
    estado_a = actualizar_estado(estado_a, percepcion_final)

    # Historia B: hora previa de presión baja -> racha vuelve a arrancar en 1.
    estado_b = crear_estado_inicial()
    estado_b = actualizar_estado(estado_b, _percepcion(hora=9, presion=0.3))
    estado_b = actualizar_estado(estado_b, percepcion_final)

    accion_simple_a, _ = decidir_reactivo_simple(percepcion_final)
    accion_simple_b, _ = decidir_reactivo_simple(percepcion_final)

    accion_modelo_a, _ = decidir_reactivo_modelo(estado_a)
    accion_modelo_b, _ = decidir_reactivo_modelo(estado_b)

    # El agente reactivo simple ignora la historia: misma acción siempre.
    assert accion_simple_a == accion_simple_b == "RECOMENDAR_REFUERZO"

    # El agente basado en modelo puede diferir porque su estado difiere.
    assert accion_modelo_a == "RECOMENDAR_REFUERZO"
    assert accion_modelo_b == "NO_REFORZAR"
    assert accion_modelo_a != accion_modelo_b


# Ninguna función de decisión recibe o consulta datos de h+1.
def test_funciones_no_reciben_datos_futuros():
    for funcion in (decidir_reactivo_simple, actualizar_estado, decidir_reactivo_modelo):
        parametros = inspect.signature(funcion).parameters
        for nombre in parametros:
            assert "futuro" not in nombre
            assert "h_mas_1" not in nombre
            assert "resultado" not in nombre


def test_procesar_secuencia_no_usa_columnas_futuras():
    percepciones = pd.DataFrame(
        [
            _percepcion(hora=8, presion=0.4),
            _percepcion(hora=9, presion=0.9),
            _percepcion(hora=10, presion=0.95),
        ]
    )
    columnas_prohibidas = {"necesita_refuerzo", "taxis_adicionales_sugeridos"}
    assert columnas_prohibidas.isdisjoint(percepciones.columns)

    bitacora = procesar_secuencia(percepciones)

    assert list(bitacora["hora"]) == [8, 9, 10]
    assert list(bitacora["accion_simple"]) == [
        "NO_REFORZAR",
        "RECOMENDAR_REFUERZO",
        "RECOMENDAR_REFUERZO",
    ]
    assert list(bitacora["accion_modelo"]) == [
        "NO_REFORZAR",
        "NO_REFORZAR",
        "RECOMENDAR_REFUERZO",
    ]
    assert list(bitacora["racha_presion_alta"]) == [0, 1, 2]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))