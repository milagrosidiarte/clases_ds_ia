"""Plantilla para el trabajo practico de agentes de movilidad.

Complete las funciones marcadas con TODO sin consultar datos de h+1.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd


ACCIONES = {"NO_REFORZAR", "RECOMENDAR_REFUERZO", "ABSTENERSE"}
UMBRAL_PRESION = 0.85

# Campos que deben estar presentes y ser numéricos válidos para decidir.
CAMPOS_REQUERIDOS = (
    "hora",
    "taxis_x",
    "demanda_total",
    "demanda_x",
    "capacidad_x",
    "presion",
)


def _es_numero_invalido(valor: Any) -> bool:
    """True si el valor no es un número usable (None, NaN, tipo incorrecto)."""
    if valor is None:
        return True
    if isinstance(valor, bool):  # bool es subclase de int, lo descarto
        return True
    if not isinstance(valor, (int, float)):
        return True
    if isinstance(valor, float) and math.isnan(valor):
        return True
    return False


def _percepcion_valida(percepcion: dict[str, Any]) -> bool:
    """Verifica que la percepción tenga los datos mínimos para decidir.
    capacidad_x == 0 es válido (zona sin flota propia); lo inválido es
    None/NaN o negativos.
    """
    if not isinstance(percepcion, dict):
        return False

    for campo in CAMPOS_REQUERIDOS:
        if campo not in percepcion or _es_numero_invalido(percepcion[campo]):
            return False

    for campo in ("hora", "taxis_x", "demanda_total", "demanda_x", "capacidad_x"):
        if percepcion[campo] < 0:
            return False

    if percepcion["presion"] < 0:
        return False

    return True


def decidir_reactivo_simple(percepcion: dict[str, Any]) -> tuple[str, str]:
    """Devuelve (accion, motivo) usando solo la percepcion actual."""
    if not _percepcion_valida(percepcion):
        return (
            "ABSTENERSE",
            "Percepción inválida: faltan datos requeridos, hay valores "
            "inválidos o la capacidad de X es desconocida.",
        )

    presion = percepcion["presion"]
    if presion >= UMBRAL_PRESION:
        return (
            "RECOMENDAR_REFUERZO",
            f"presion={presion:.2f} >= umbral {UMBRAL_PRESION} en la hora actual.",
        )
    return (
        "NO_REFORZAR",
        f"presion={presion:.2f} < umbral {UMBRAL_PRESION} en la hora actual.",
    )


def crear_estado_inicial() -> dict[str, Any]:
    """Crea el estado persistente del agente reactivo basado en modelo."""
    return {
        "percepcion_valida": False,
        "racha_presion_alta": 0,
        "presion_anterior": None,
        "ultima_accion": None,
    }


def actualizar_estado(
    estado_anterior: dict[str, Any],
    percepcion: dict[str, Any],
) -> dict[str, Any]:
    """Actualiza la memoria a partir del estado anterior y la percepcion."""
    nuevo_estado = dict(estado_anterior)
    valida = _percepcion_valida(percepcion)
    nuevo_estado["percepcion_valida"] = valida

    if not valida:
        nuevo_estado["racha_presion_alta"] = 0
        nuevo_estado["presion_anterior"] = None
        return nuevo_estado

    presion = percepcion["presion"]
    if presion >= UMBRAL_PRESION:
        nuevo_estado["racha_presion_alta"] = (
            estado_anterior.get("racha_presion_alta", 0) + 1
        )
    else:
        nuevo_estado["racha_presion_alta"] = 0

    nuevo_estado["presion_anterior"] = presion
    return nuevo_estado


def decidir_reactivo_modelo(
    estado_actual: dict[str, Any],
) -> tuple[str, str]:
    """Devuelve (accion, motivo) a partir del estado interno actualizado."""
    if not estado_actual.get("percepcion_valida", False):
        return (
            "ABSTENERSE",
            "Estado inválido: la última percepción no pudo validarse.",
        )

    racha = estado_actual.get("racha_presion_alta", 0)
    if racha >= 2:
        return (
            "RECOMENDAR_REFUERZO",
            f"racha_presion_alta={racha} (>=2 horas consecutivas con presión alta).",
        )
    return (
        "NO_REFORZAR",
        f"racha_presion_alta={racha} (<2 horas consecutivas con presión alta).",
    )


def procesar_secuencia(percepciones: pd.DataFrame) -> pd.DataFrame:
    """Ejecuta ambos agentes y construye la bitacora comparativa."""
    estado = crear_estado_inicial()
    filas: list[dict[str, Any]] = []

    for _, fila in percepciones.sort_values("hora").iterrows():
        percepcion = fila.to_dict()

        accion_simple, motivo_simple = decidir_reactivo_simple(percepcion)

        estado = actualizar_estado(estado, percepcion)
        accion_modelo, motivo_modelo = decidir_reactivo_modelo(estado)
        estado["ultima_accion"] = accion_modelo

        filas.append(
            {
                "hora": percepcion.get("hora"),
                "presion": percepcion.get("presion"),
                "racha_presion_alta": estado["racha_presion_alta"],
                "accion_simple": accion_simple,
                "motivo_simple": motivo_simple,
                "accion_modelo": accion_modelo,
                "motivo_modelo": motivo_modelo,
            }
        )

    return pd.DataFrame(filas)