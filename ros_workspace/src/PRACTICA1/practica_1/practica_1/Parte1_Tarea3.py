#!/usr/bin/python3
"""Parte 1, tarea 3: calcular y guardar datos cinemáticos con su tiempo."""

from __future__ import annotations

import csv
from datetime import datetime
from math import isfinite, nan
from pathlib import Path
from threading import Condition
from typing import TYPE_CHECKING, Optional, TextIO

if TYPE_CHECKING:
    from sensor_msgs.msg import JointState

    from practica_1.Parte2_Tarea1 import PublicadorDatos

NANOSEGUNDOS_POR_SEGUNDO = 1_000_000_000
COLUMNAS = [
    'segundos', 'nanosegundos', 'tiempo_relativo_s', 'trayectoria',
    'articulacion', 'posicion_rad', 'velocidad_rad_s', 'aceleracion_rad_s2',
]


class RegistroDatos:
    """Calcula derivadas y escribe una fila por articulación y muestra."""

    def __init__(self, articulaciones: list[str],
                 directorio: str = 'datos_practica_1',
                 publicador: Optional[PublicadorDatos] = None) -> None:
        """Crea una carpeta por ejecución para no sobrescribir resultados."""
        self.articulaciones = list(articulaciones)
        self.publicador = publicador
        fecha = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        self.directorio = Path(directorio) / fecha
        self.directorio.mkdir(parents=True)
        self.muestras_guardadas = 0
        # Los callbacks y el hilo principal comparten archivo e historial.
        self._bloqueo = Condition()
        self._archivo: Optional[TextIO] = None
        self._escritor = None
        self._trayectoria = ''
        self._inicio_ns = 0
        self._ultimo_ns: Optional[int] = None
        self._posiciones_anteriores: list[float] = []
        self._velocidades_anteriores: list[float] = []

    def iniciar_trayectoria(self, nombre: str, marca_ns: int) -> None:
        """Abre el CSV y reinicia las derivadas de la trayectoria."""
        with self._bloqueo:
            if self._archivo is not None:
                raise RuntimeError('Hay una trayectoria sin cerrar.')
            self._archivo = (self.directorio / f'{nombre}.csv').open(
                'x', newline='', encoding='utf-8'
            )
            self._escritor = csv.writer(self._archivo)
            self._escritor.writerow(COLUMNAS)
            self._trayectoria = nombre
            self._inicio_ns = marca_ns
            self._ultimo_ns = None
            self._posiciones_anteriores = []
            self._velocidades_anteriores = []
            self.muestras_guardadas = 0

    def _debe_guardar(self, velocidades: list[float]) -> bool:
        """La parte mínima guarda todas las muestras válidas del movimiento."""
        return True

    def procesar(self, mensaje: JointState, marca_ns: int) -> None:
        """Ordena por nombre, deriva con el tiempo y guarda la muestra."""
        with self._bloqueo:
            if self._archivo is None or marca_ns < self._inicio_ns:
                return
            if self._ultimo_ns is not None and marca_ns <= self._ultimo_ns:
                return  # Una marca repetida o atrasada no sirve para derivar.

            indices = {nombre: i for i, nombre in enumerate(mensaje.name)}
            if any(nombre not in indices for nombre in self.articulaciones):
                return
            if any(indices[nombre] >= len(mensaje.position)
                   for nombre in self.articulaciones):
                return
            posiciones = [float(mensaje.position[indices[nombre]])
                          for nombre in self.articulaciones]
            if not all(isfinite(posicion) for posicion in posiciones):
                return

            velocidades = [nan] * len(self.articulaciones)
            aceleraciones = [nan] * len(self.articulaciones)
            if self._ultimo_ns is not None:
                intervalo = ((marca_ns - self._ultimo_ns)
                             / NANOSEGUNDOS_POR_SEGUNDO)
                # El hardware mock puede publicar velocidad 0 en movimiento.
                velocidades = [(actual - anterior) / intervalo
                               for actual, anterior in
                               zip(posiciones, self._posiciones_anteriores)]
                aceleraciones = [
                    (actual - anterior) / intervalo
                    for actual, anterior in
                    zip(velocidades, self._velocidades_anteriores)
                ]

            # El historial en reposo permite detectar el siguiente arranque.
            self._ultimo_ns = marca_ns
            self._posiciones_anteriores = posiciones
            self._velocidades_anteriores = velocidades
            self._bloqueo.notify_all()
            if not self._debe_guardar(velocidades):
                return

            segundos, nanosegundos = divmod(marca_ns, NANOSEGUNDOS_POR_SEGUNDO)
            tiempo = (marca_ns - self._inicio_ns) / NANOSEGUNDOS_POR_SEGUNDO
            for nombre, posicion, velocidad, aceleracion in zip(
                    self.articulaciones, posiciones,
                    velocidades, aceleraciones):
                self._escritor.writerow([
                    segundos, nanosegundos, tiempo, self._trayectoria,
                    nombre, posicion, velocidad, aceleracion,
                ])
            if self.publicador is not None:
                self.publicador.publicar_datos(
                    self._trayectoria, marca_ns, self.articulaciones,
                    posiciones, velocidades, aceleraciones,
                )
            self.muestras_guardadas += 1

    def esperar_muestra(self, marca_ns: int, espera: float = 2.0) -> bool:
        """Espera la última muestra antes de cerrar el CSV."""
        with self._bloqueo:
            return self._bloqueo.wait_for(
                lambda: (self._ultimo_ns is not None
                         and self._ultimo_ns >= marca_ns),
                timeout=espera,
            )

    def cerrar_trayectoria(self) -> int:
        """Cierra el archivo y devuelve el número de muestras guardadas."""
        with self._bloqueo:
            if self._archivo is not None:
                self._archivo.close()
                self._archivo = None
                self._escritor = None
            return self.muestras_guardadas
