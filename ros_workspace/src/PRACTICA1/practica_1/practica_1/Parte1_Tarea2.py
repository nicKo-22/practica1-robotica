#!/usr/bin/python3
"""Parte 1, tarea 2: ejecutar movimientos joint, lineal y circular."""

from copy import deepcopy
from math import cos, pi, sin
from typing import Callable

from pruebas.control_robot import ControlRobot

from practica_1.Parte1_Tarea3 import RegistroDatos

ARTICULACIONES_INICIALES = [0, -pi / 2, -pi / 2, -pi / 2, pi / 2, 0]
GIRO_JOINT = pi / 6  # radianes
DESPLAZAMIENTO_LINEAL = 0.05  # metros, hacia arriba
RADIO_CIRCULO = 0.03  # metros
PUNTOS_CIRCULO = 64


class Trayectorias(ControlRobot):
    """Hereda los movimientos, clientes de MoveIt y ejecutor del ejemplo."""

    def movimiento_joint(self) -> bool:
        """Gira la primera articulación conservando el resto de posiciones."""
        articulaciones = self.articulaciones_actuales()
        articulaciones[0] += GIRO_JOINT
        return self.mover_articulaciones(articulaciones)

    def movimiento_lineal(self) -> bool:
        """Eleva el efector en línea recta manteniendo su orientación."""
        pose_actual = self.pose_actual()
        pose_actual.position.z += DESPLAZAMIENTO_LINEAL
        return self.mover_trayectoria([pose_actual])

    def movimiento_circular(self) -> bool:
        """Aproxima una circunferencia XY con segmentos cartesianos."""
        pose_inicio = self.pose_actual()
        poses = []
        for punto in range(1, PUNTOS_CIRCULO + 1):
            angulo = 2 * pi * punto / PUNTOS_CIRCULO
            pose_actual = deepcopy(pose_inicio)
            # El centro queda un radio a la izquierda de la pose inicial.
            pose_actual.position.x += RADIO_CIRCULO * (cos(angulo) - 1)
            pose_actual.position.y += RADIO_CIRCULO * sin(angulo)
            poses.append(deepcopy(pose_actual))
        return self.mover_trayectoria(poses)

    def _ejecutar_trayectoria(self, nombre: str,
                             movimiento: Callable[[], bool],
                             registro: RegistroDatos) -> None:
        """Abre un CSV por movimiento y espera su última muestra."""
        self.get_logger().info(f'Ejecutando trayectoria {nombre}')
        marca_ns = self.get_clock().now().nanoseconds
        registro.iniciar_trayectoria(nombre, marca_ns)
        try:
            if not movimiento():
                raise RuntimeError(f'MoveIt no completó {nombre}.')
            # Evita cerrar el CSV antes de atender los últimos JointState.
            marca_ns = self.get_clock().now().nanoseconds
            if not registro.esperar_muestra(marca_ns):
                raise RuntimeError(f'No llegan muestras al terminar {nombre}.')
        finally:
            muestras = registro.cerrar_trayectoria()

        if muestras == 0:
            raise RuntimeError(f'{nombre} no tiene datos guardados.')
        self.get_logger().info(f'{nombre}: {muestras} muestras guardadas')

    def ejecutar(self, registro: RegistroDatos) -> None:
        """Lleva el robot al inicio y registra las tres trayectorias."""
        # La colocación inicial no forma parte de las tres trayectorias.
        if not self.mover_articulaciones(ARTICULACIONES_INICIALES):
            raise RuntimeError('No se pudo alcanzar la posición inicial.')

        self._ejecutar_trayectoria('joint', self.movimiento_joint, registro)
        self._ejecutar_trayectoria('lineal', self.movimiento_lineal, registro)
        self._ejecutar_trayectoria('circular', self.movimiento_circular,
                                  registro)
