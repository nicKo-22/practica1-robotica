#!/usr/bin/python3
"""Parte 1, tarea 1: leer el estado de las articulaciones en tiempo real."""

from typing import Optional

import rclpy
from pruebas.suscriptor_basico import Suscriptor
from sensor_msgs.msg import JointState

from practica_1.Parte1_Tarea3 import RegistroDatos

NANOSEGUNDOS_POR_SEGUNDO = 1_000_000_000


class SuscriptorArticulaciones(Suscriptor):
    """Reutiliza el suscriptor básico para recibir mensajes JointState."""

    def __init__(self, registro: Optional[RegistroDatos] = None) -> None:
        """Recibe un registro o muestra las posiciones en la terminal."""
        self.registro = registro
        super().__init__(JointState, '/joint_states',
                         'suscriptor_articulaciones')

    def callback(self, mensaje: JointState) -> None:
        """Entrega al registro la muestra y su tiempo de simulación."""
        if self.registro is None:
            articulaciones = list(zip(mensaje.name, mensaje.position))
            print(f'Articulaciones: {articulaciones}')
            return

        marca_ns = (
            mensaje.header.stamp.sec * NANOSEGUNDOS_POR_SEGUNDO
            + mensaje.header.stamp.nanosec
        )
        if marca_ns == 0:
            marca_ns = self.get_clock().now().nanoseconds
        self.registro.procesar(mensaje, marca_ns)


def main(args: Optional[list[str]] = None) -> None:
    """Ejecuta únicamente el suscriptor, como en suscriptor_basico.py."""
    rclpy.init(args=args)
    nodo = SuscriptorArticulaciones()
    try:
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass
    finally:
        nodo.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
