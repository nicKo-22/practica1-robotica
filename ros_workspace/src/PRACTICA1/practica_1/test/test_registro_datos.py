"""Comprueba derivadas y CSV con muestras sintéticas, sin necesitar ROS."""

import csv
import math
import tempfile
import unittest
from threading import Thread
from types import SimpleNamespace
from unittest.mock import Mock

from practica_1.Parte1_Tarea3 import RegistroDatos
from practica_1.Parte2_Tarea2 import IngestaInteligente

ARTICULACIONES = [
    'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
    'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint',
]
SEGUNDO = 1_000_000_000


def estado(posicion: float) -> SimpleNamespace:
    """Desordena las seis articulaciones y añade una articulación de pinza."""
    valores = {nombre: posicion * (i + 1)
               for i, nombre in enumerate(ARTICULACIONES)}
    valores['pinza'] = 99.0
    nombres = list(reversed(valores))
    return SimpleNamespace(
        name=nombres,
        position=[valores[nombre] for nombre in nombres],
        velocity=[0.0] * len(nombres),
    )


class TestRegistroDatos(unittest.TestCase):
    """Verifica resultados físicos, separación de trayectorias y reposo."""

    def setUp(self) -> None:
        """Aísla los CSV de cada prueba en un directorio temporal."""
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)

    def crear_registro(self, inteligente: bool = False,
                       publicador: Mock | None = None) -> RegistroDatos:
        """Crea un registro y programa su cierre al acabar la prueba."""
        clase = IngestaInteligente if inteligente else RegistroDatos
        registro = clase(ARTICULACIONES, self.temporal.name, publicador)
        self.addCleanup(registro.cerrar_trayectoria)
        return registro

    def leer(self, registro: RegistroDatos,
             trayectoria: str = 'joint') -> list[dict[str, str]]:
        """Cierra el archivo antes de comprobar su contenido en disco."""
        registro.cerrar_trayectoria()
        ruta = registro.directorio / f'{trayectoria}.csv'
        with ruta.open(encoding='utf-8', newline='') as archivo:
            return list(csv.DictReader(archivo))

    def test_derivadas_orden_y_marca_temporal(self) -> None:
        """q = 0, 1, 3 rad produce v = 1, 2 rad/s y a = 1 rad/s²."""
        registro = self.crear_registro()
        inicio = SEGUNDO + 123_456_789
        registro.iniciar_trayectoria('joint', inicio)
        for i, posicion in enumerate([0.0, 1.0, 3.0]):
            registro.procesar(estado(posicion), inicio + i * SEGUNDO)
        filas = self.leer(registro)
        self.assertEqual(len(filas), 18)
        self.assertEqual([fila['articulacion'] for fila in filas[:6]],
                         ARTICULACIONES)
        self.assertTrue(math.isnan(float(filas[0]['velocidad_rad_s'])))
        self.assertTrue(math.isnan(float(filas[6]['aceleracion_rad_s2'])))
        for i, fila in enumerate(filas[-6:]):
            self.assertAlmostEqual(float(fila['posicion_rad']), 3 * (i + 1))
            self.assertAlmostEqual(float(fila['velocidad_rad_s']), 2 * (i + 1))
            self.assertAlmostEqual(float(fila['aceleracion_rad_s2']), i + 1)
            self.assertEqual(fila['segundos'], '3')
            self.assertEqual(fila['nanosegundos'], '123456789')
            self.assertEqual(fila['tiempo_relativo_s'], '2.0')

    def test_intervalos_no_uniformes(self) -> None:
        """Las diferencias usan el tiempo real de cada par de muestras."""
        registro = self.crear_registro()
        registro.iniciar_trayectoria('joint', SEGUNDO)
        for marca, posicion in [(1.0, 0.0), (1.5, 1.0), (1.75, 1.75)]:
            registro.procesar(estado(posicion), int(marca * SEGUNDO))
        ultima = self.leer(registro)[-6]
        self.assertAlmostEqual(float(ultima['velocidad_rad_s']), 3.0)
        self.assertAlmostEqual(float(ultima['aceleracion_rad_s2']), 4.0)

    def test_reposo_arranque_parada_y_rearranque(self) -> None:
        """No guarda pausas y conserva el historial para el rearranque."""
        publicador = Mock()
        registro = self.crear_registro(True, publicador)
        registro.iniciar_trayectoria('joint', SEGUNDO)
        posiciones = [0.0, 0.0, 0.1, 0.2, 0.2, 0.2, 0.3]
        for i, posicion in enumerate(posiciones, start=1):
            registro.procesar(estado(posicion), i * SEGUNDO)
        filas = self.leer(registro)
        self.assertEqual(registro.muestras_guardadas, 3)
        self.assertEqual(len(filas), 18)
        self.assertEqual({fila['segundos'] for fila in filas}, {'3', '4', '7'})
        self.assertAlmostEqual(float(filas[-6]['velocidad_rad_s']), 0.1)
        self.assertEqual(publicador.publicar_datos.call_count, 3)

    def test_reposo_total_y_ruido_no_se_guardan(self) -> None:
        """Un desplazamiento bajo el umbral no genera filas ni mensajes."""
        publicador = Mock()
        registro = self.crear_registro(True, publicador)
        registro.iniciar_trayectoria('joint', SEGUNDO)
        for i, posicion in enumerate([0.0, 0.0, 0.00001], start=1):
            registro.procesar(estado(posicion), i * SEGUNDO)
        self.assertEqual(self.leer(registro), [])
        publicador.publicar_datos.assert_not_called()

    def test_descarta_tiempos_repetidos_y_anteriores(self) -> None:
        """Una muestra descartada no altera la derivada de la siguiente."""
        registro = self.crear_registro()
        registro.iniciar_trayectoria('joint', 2 * SEGUNDO)
        for marca, posicion in [(1, 100), (2, 0), (2, 100), (1, 100), (3, 1)]:
            registro.procesar(estado(posicion), marca * SEGUNDO)
        filas = self.leer(registro)
        self.assertEqual(len(filas), 12)
        self.assertAlmostEqual(float(filas[-6]['velocidad_rad_s']), 1.0)

    def test_descarta_muestras_incompletas_o_no_finitas(self) -> None:
        """Los mensajes parciales y de la pinza no generan datos del brazo."""
        registro = self.crear_registro()
        registro.iniciar_trayectoria('joint', SEGUNDO)
        registro.procesar(estado(0.0), SEGUNDO)
        invalidos = [
            SimpleNamespace(name=['pinza'], position=[1.0]),
            SimpleNamespace(name=ARTICULACIONES, position=[]),
            estado(math.nan),
            estado(math.inf),
        ]
        for mensaje in invalidos:
            registro.procesar(mensaje, 2 * SEGUNDO)
        registro.procesar(estado(2.0), 3 * SEGUNDO)
        filas = self.leer(registro)
        self.assertEqual(len(filas), 12)
        self.assertAlmostEqual(float(filas[-6]['velocidad_rad_s']), 1.0)

    def test_trayectorias_independientes_y_sin_sobrescritura(self) -> None:
        """No deriva entre archivos y rechaza sobrescribir un CSV existente."""
        registro = self.crear_registro()
        registro.iniciar_trayectoria('joint', SEGUNDO)
        registro.procesar(estado(0.0), SEGUNDO)
        registro.procesar(estado(1.0), 2 * SEGUNDO)
        primeras = self.leer(registro)
        registro.iniciar_trayectoria('lineal', 20 * SEGUNDO)
        registro.procesar(estado(100.0), 20 * SEGUNDO)
        segundas = self.leer(registro, 'lineal')
        self.assertEqual({fila['trayectoria'] for fila in primeras}, {'joint'})
        self.assertEqual({fila['trayectoria'] for fila in segundas},
                         {'lineal'})
        self.assertTrue(math.isnan(float(segundas[0]['velocidad_rad_s'])))
        with self.assertRaises(FileExistsError):
            registro.iniciar_trayectoria('joint', 30 * SEGUNDO)

    def test_publica_la_misma_muestra_completa_del_csv(self) -> None:
        """Las seis articulaciones conservan su orden al publicar."""
        publicador = Mock()
        registro = self.crear_registro(publicador=publicador)
        registro.iniciar_trayectoria('circular', SEGUNDO)
        for i, posicion in enumerate([0.0, 1.0, 3.0], start=1):
            registro.procesar(estado(posicion), i * SEGUNDO)
        argumentos = publicador.publicar_datos.call_args.args
        self.assertEqual(argumentos[:3],
                         ('circular', 3 * SEGUNDO, ARTICULACIONES))
        self.assertEqual(argumentos[3], [3.0 * i for i in range(1, 7)])
        self.assertEqual(argumentos[4], [2.0 * i for i in range(1, 7)])
        self.assertEqual(argumentos[5], [float(i) for i in range(1, 7)])

    def test_espera_a_la_ultima_muestra_del_callback(self) -> None:
        """El hilo principal espera hasta procesar la última muestra."""
        registro = self.crear_registro()
        registro.iniciar_trayectoria('joint', SEGUNDO)
        self.assertFalse(registro.esperar_muestra(SEGUNDO, espera=0))
        hilo = Thread(target=registro.procesar, args=(estado(0.0), SEGUNDO))
        hilo.start()
        try:
            self.assertTrue(registro.esperar_muestra(SEGUNDO, espera=1))
        finally:
            hilo.join()

    def test_sin_trayectoria_no_guarda(self) -> None:
        """La colocación inicial y los datos tras el cierre se ignoran."""
        registro = self.crear_registro()
        registro.procesar(estado(100.0), SEGUNDO)
        registro.iniciar_trayectoria('joint', 2 * SEGUNDO)
        registro.procesar(estado(0.0), 2 * SEGUNDO)
        registro.cerrar_trayectoria()
        registro.procesar(estado(100.0), 3 * SEGUNDO)
        self.assertEqual(len(self.leer(registro)), 6)

    def test_umbral_invalido(self) -> None:
        """Un umbral negativo, infinito o NaN no es válido."""
        for umbral in [-1.0, math.nan, math.inf]:
            with self.subTest(umbral=umbral), self.assertRaises(ValueError):
                IngestaInteligente(ARTICULACIONES, self.temporal.name,
                                  umbral=umbral)


if __name__ == '__main__':
    unittest.main()
