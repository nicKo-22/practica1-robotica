#!/usr/bin/python3
"""Parte 1, tarea 1: leer el estado de las articulaciones en tiempo real."""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class Suscriptor(Node):
    """Recibe el estado de las articulaciones y lo muestra en la terminal."""

    def __init__(self) -> None:
        super().__init__("suscriptor_articulaciones")
        # Topic y tipo de mensaje utilizados también en control_robot.py.
        self.create_subscription(JointState, "/joint_states", self.callback, 10)

    def callback(self, mensaje: JointState) -> None:
        """Muestra los datos de cada mensaje recibido, sin calcular ni guardar."""
        print(f"\nArticulaciones: {mensaje.name}")
        print(f"Posiciones (rad): {list(mensaje.position)}")
        print(f"Velocidades (rad/s): {list(mensaje.velocity)}")
        print(f"Esfuerzos (N.m): {list(mensaje.effort)}")


if __name__ == '__main__':
    rclpy.init()
    nodo = Suscriptor()
    try:
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass
    finally:
        nodo.destroy_node()
        rclpy.try_shutdown()
