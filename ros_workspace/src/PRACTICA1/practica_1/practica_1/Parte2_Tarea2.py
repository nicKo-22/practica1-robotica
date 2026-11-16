#!/usr/bin/python3
"""Parte 2, reto 2: guardar y publicar solo cuando se detecta movimiento."""

from __future__ import annotations

from math import isfinite
from typing import TYPE_CHECKING, Optional

from practica_1.Parte1_Tarea3 import RegistroDatos

if TYPE_CHECKING:
    from practica_1.Parte2_Tarea1 import PublicadorDatos

UMBRAL_VELOCIDAD = 0.001  


class IngestaInteligente(RegistroDatos):
    """Añade un filtro de movimiento sin duplicar el cálculo ni el CSV."""

    def __init__(self, articulaciones: list[str],
                 directorio: str = 'datos_practica_1',
                 publicador: Optional[PublicadorDatos] = None,
                 umbral: float = UMBRAL_VELOCIDAD) -> None:
        """Ajusta la sensibilidad del filtro a los datos del robot."""
        if not isfinite(umbral) or umbral < 0:
            raise ValueError('El umbral debe ser finito y no negativo.')
        self.umbral = umbral
        super().__init__(articulaciones, directorio, publicador)

    def _debe_guardar(self, velocidades: list[float]) -> bool:
        """Basta con que una articulación supere el umbral de velocidad."""
        return any(isfinite(velocidad) and abs(velocidad) > self.umbral
                   for velocidad in velocidades)
