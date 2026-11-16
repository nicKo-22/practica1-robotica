#!/usr/bin/python3
"""Conecta las cinco tareas y ejecuta la práctica completa."""

from typing import Optional

import rclpy

from practica_1.Parte1_Tarea1 import SuscriptorArticulaciones
from practica_1.Parte1_Tarea2 import Trayectorias
from practica_1.Parte1_Tarea3 import RegistroDatos
from practica_1.Parte2_Tarea1 import PublicadorDatos
from practica_1.Parte2_Tarea2 import IngestaInteligente, UMBRAL_VELOCIDAD


def main(args: Optional[list[str]] = None) -> None:
    """Comparte el ejecutor de ControlRobot para atender los tres nodos ROS."""
    rclpy.init(args=args)
    control = None
    suscriptor = None
    publicador = None
    registro = None
    try:
        suscriptor = SuscriptorArticulaciones()
        directorio = suscriptor.declare_parameter(
            'directorio_salida', 'datos_practica_1'
        ).value
        filtrar = suscriptor.declare_parameter(
            'ingesta_inteligente', True
        ).value
        umbral = suscriptor.declare_parameter(
            'umbral_velocidad', UMBRAL_VELOCIDAD
        ).value

        control = Trayectorias()
        publicador = PublicadorDatos()
        if filtrar:
            registro = IngestaInteligente(
                control.articulaciones, directorio, publicador, umbral
            )
        else:
            registro = RegistroDatos(control.articulaciones, directorio,
                                     publicador)

        suscriptor.registro = registro
        control.ejecutor.add_node(suscriptor)
        control.ejecutor.add_node(publicador)
        suscriptor.get_logger().info(f'Datos: {registro.directorio.resolve()}')
        control.ejecutar(registro)
    except KeyboardInterrupt:
        if suscriptor is not None:
            suscriptor.get_logger().warning(
                'Práctica interrumpida; datos parciales.'
            )
    except Exception:
        if suscriptor is not None:
            suscriptor.get_logger().error(
                'Práctica incompleta. Los CSV pueden contener datos parciales.'
            )
        raise
    finally:
        if control is not None:
            control.ejecutor.shutdown()
        if registro is not None:
            registro.cerrar_trayectoria()
        for nodo in (publicador, suscriptor, control):
            if nodo is not None:
                nodo.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
