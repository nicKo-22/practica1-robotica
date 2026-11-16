#!/usr/bin/python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Publicador(Node):
    """Publicador del ejemplo, reutilizable con otro mensaje y otro topic."""

    def __init__(self, tipo_mensaje: type = String,
                 topic: str = "primer_topic", periodo: float | None = 0.1,
                 nombre_nodo: str = "publicador_basico") -> None:
        """Un periodo None permite publicar solo al recibir nuevos datos."""
        super().__init__(nombre_nodo)
        self.publicador = self.create_publisher(tipo_mensaje, topic, 10)
        if periodo is not None:
            self.create_timer(periodo, self.publicar)  # 10 Hz por defecto

    def publicar(self):
        mensaje = String()
        mensaje.data = f"Hola Mundo {self.get_clock().now().nanoseconds / 1e9}"
        self.publicador.publish(mensaje)


if __name__ == '__main__':
    rclpy.init()
    nodo = Publicador()
    try:
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass
    nodo.destroy_node()
    rclpy.try_shutdown()
