"""Parte 2, reto 1: publicar los datos en un mensaje ROS personalizado."""

from pruebas.publicador_basico import Publicador
from practica_1_interfaces.msg import DatosCinematicos

NANOSEGUNDOS_POR_SEGUNDO = 1_000_000_000


class PublicadorDatos(Publicador):
    """Hereda el publicador básico y publica al calcular una nueva muestra."""

    def __init__(self) -> None:
        """Crea el topic cinemático sin el temporizador de Hola Mundo."""
        super().__init__(DatosCinematicos, '/datos_cinematicos', periodo=None,
                         nombre_nodo='publicador_datos')

    def publicar_datos(self, trayectoria: str, marca_ns: int,
                       articulaciones: list[str], posiciones: list[float],
                       velocidades: list[float],
                       aceleraciones: list[float]) -> None:
        """Empaqueta las seis articulaciones con la misma marca temporal."""
        mensaje = DatosCinematicos()
        mensaje.stamp.sec, mensaje.stamp.nanosec = divmod(
            marca_ns, NANOSEGUNDOS_POR_SEGUNDO
        )
        mensaje.trayectoria = trayectoria
        mensaje.articulaciones = list(articulaciones)
        mensaje.posiciones = list(posiciones)
        mensaje.velocidades = list(velocidades)
        mensaje.aceleraciones = list(aceleraciones)
        self.publicador.publish(mensaje)
