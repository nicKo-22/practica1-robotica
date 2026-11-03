"""Punto de entrada: conecta las tareas de la práctica en un mismo nodo."""

import threading
from typing import Optional

import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from practica_1.tarea_1_suscriptor import SuscriptorArticulaciones
from practica_1.tarea_2_control_robot import ControlRobot
from practica_1.tarea_2_trayectorias import Trayectorias
from practica_1.tarea_3_procesamiento import RegistroDatos


class Practica(Node):
    """Reúne el suscriptor, el control del robot y el registro de datos."""

    def __init__(self) -> None:
        super().__init__('practica_1')
        registro = RegistroDatos(self)
        self._suscriptor = SuscriptorArticulaciones(self, registro)
        control = ControlRobot(self, registro)
        self.trayectorias = Trayectorias(self, control, registro)


def main(args: Optional[list[str]] = None) -> None:
    """Ejecuta las trayectorias mientras ROS atiende los mensajes recibidos."""
    rclpy.init(args=args)
    nodo = Practica()
    ejecutor = MultiThreadedExecutor()
    ejecutor.add_node(nodo)
    hilo = threading.Thread(target=ejecutor.spin, daemon=True)
    hilo.start()
    try:
        nodo.trayectorias.ejecutar()
    except (RuntimeError, KeyboardInterrupt) as error:
        nodo.get_logger().error(f'Práctica interrumpida: {error}')
        raise
    finally:
        ejecutor.shutdown()
        hilo.join()
        nodo.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
