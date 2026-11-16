#!/usr/bin/python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Suscriptor(Node):
    """Suscriptor del ejemplo, reutilizable con otro mensaje y otro topic."""

    def __init__(self, tipo_mensaje: type = String,
                 topic: str = "primer_topic",
                 nombre_nodo: str = "suscriptor_basico") -> None:
        """Sin argumentos conserva el comportamiento del ejemplo original."""
        super().__init__(nombre_nodo)
        self.create_subscription(tipo_mensaje, topic, self.callback, 10)

    def callback(self, mensaje: String):
        print(f"He recibido: {mensaje.data}")


if __name__ == '__main__':
    rclpy.init()
    nodo = Suscriptor()
    try:
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass
    nodo.destroy_node()
    rclpy.try_shutdown()
