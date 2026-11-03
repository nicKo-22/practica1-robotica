"""Nombres y parámetros utilizados por el control y el registro del UR3e."""

ARTICULACIONES = (
    'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
    'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint',
)
GRUPO = 'robot'
REFERENCIA = 'world'
EFECTOR = 'wrist_3_link'
ESCALA = 0.1
UMBRAL_VELOCIDAD = 0.001  # rad/s; evita guardar pequeñas oscilaciones en reposo.
ESPERA_SERVIDOR = 30.0  # segundos
RADIO_CIRCULO = 0.03  # metros
PUNTOS_CIRCULO = 32
