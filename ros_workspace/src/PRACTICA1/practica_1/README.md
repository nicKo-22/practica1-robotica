# Práctica 1: datos cinemáticos del UR3e

Esta práctica registra las seis articulaciones del brazo durante tres movimientos:
articular (`joint`), rectilíneo (`lineal`) y circular (`circular`). Antes, el
programa lleva el robot a una posición inicial sin guardar datos. Los movimientos
están pensados para la **simulación de un solo robot**, por ejemplo el 203.

## 1. Arrancar el entorno

Desde PowerShell, en la carpeta principal del repositorio:

```powershell
.\lab.bat iniciar
```

Espera a que Docker y el entorno estén disponibles. En el escritorio del
contenedor o en VS Code conectado a él, abre terminales Linux para los siguientes
pasos. En Windows también puedes abrir una terminal del contenedor ejecutando
`.\lab.bat terminal` desde otra ventana de PowerShell.

## 2. Compilar los paquetes

En una terminal del contenedor:

```bash
cd /home/laboratorio/ros_workspace
colcon build --symlink-install
source install/setup.bash
```

El primer paquete, `practica_1_interfaces`, define el mensaje personalizado.
El segundo, `practica_1`, contiene el programa Python. Compilar todo el espacio
de trabajo también deja disponibles los lanzadores de la simulación.

## 3. Lanzar la simulación

En esa terminal:

```bash
ros2 launch launcher_robots_lab_robotica sim_203.launch.py
```

Espera a que termine de arrancar MoveIt y aparezca el robot en RViz. Deja esta
terminal abierta. Para iniciar la simulación desde PowerShell también puedes
usar `.\lab.bat sim 203`.

## 4. Ejecutar la práctica

Abre una **segunda terminal del contenedor**:

```bash
cd /home/laboratorio/ros_workspace
source install/setup.bash
ros2 run practica_1 practica
```

El programa informa de cada movimiento y del número de muestras guardadas. Al
terminar, indica la ruta de una carpeta nueva como
`datos_practica_1/20261027_123456_123456/`. Contiene `joint.csv`, `lineal.csv`
y `circular.csv`. Si lo ejecutas desde otra carpeta, la salida se creará en ella.
Se puede elegir otro directorio:

```bash
ros2 run practica_1 practica --ros-args -p directorio_salida:=/home/laboratorio/ros_workspace/datos_practica_1
```

Si MoveIt no puede planificar o ejecutar un movimiento, el programa se detiene
y muestra el error; un CSV ya creado puede estar vacío o incompleto. No lo
interpretes como una trayectoria completada. Los desplazamientos se pueden
ajustar en `practica_1/tarea_2_trayectorias.py` y `practica_1/configuracion.py` si la
configuración de la escena lo exige.

## 5. Ver los datos y el mensaje

Cada fila del CSV contiene una articulación. Para cada instante hay hasta seis
filas, con segundos y nanosegundos, nombre, posición en radianes, velocidad en
rad/s y aceleración en rad/s². Por ejemplo:

```bash
head -n 10 datos_practica_1/*/joint.csv
```

Para observar el mensaje personalizado en tiempo real, abre una tercera terminal
**antes de iniciar el programa** y ejecuta:

```bash
cd /home/laboratorio/ros_workspace
source install/setup.bash
ros2 topic echo /datos_cinematicos
```

El mensaje `practica_1_interfaces/msg/DatosCinematicos` incluye el nombre de
la trayectoria y las listas de articulaciones, posiciones, velocidades y
aceleraciones. Los elementos que ocupan el mismo índice corresponden a la misma
articulación. Para ver los nodos y sus conexiones puedes ejecutar `rqt_graph`.

## 6. Cómo funciona

Los archivos dentro de `practica_1/` siguen el orden del enunciado:

1. **Suscriptor** — `tarea_1_suscriptor.py` se suscribe a `/joint_states` y
   entrega cada mensaje a `RegistroDatos.procesar`.
2. **Tres trayectorias** — `tarea_2_trayectorias.py` define los movimientos
   joint, lineal y circular. `tarea_2_control_robot.py` se comunica con MoveIt
   para planificarlos y ejecutarlos.
3. **Procesamiento** — `tarea_3_procesamiento.py` calcula y guarda los datos
   con su marca temporal en un CSV distinto para cada trayectoria.

Los retos opcionales también están implementados: el mensaje personalizado se
define en `../practica_1_interfaces/msg/DatosCinematicos.msg`, y el filtro que
ignora los periodos sin movimiento está en `RegistroDatos.procesar`.
`configuracion.py` reúne los parámetros compartidos y `practica.py` conecta
las clases y arranca el nodo. Todas comparten el mismo nodo ROS.

1. El nodo se suscribe a `/joint_states` y ordena las seis articulaciones por
   nombre. Esto evita depender del orden del mensaje recibido.
2. Antes de cada movimiento abre su CSV y lo identifica por su nombre. Cuando
   termina, lo cierra; el siguiente movimiento usa un archivo distinto.
3. Usa la marca de tiempo de `JointState`. Si es cero, usa el reloj del nodo.
   Calcula el intervalo entre muestras con esa marca y descarta marcas repetidas
   o que retrocedan. No se mezclan derivadas de trayectorias distintas.
4. Utiliza la velocidad publicada por el robot; si falta, la estima como
   `(posición actual - posición anterior) / intervalo`. La aceleración se
   estima como `(velocidad actual - velocidad anterior) / intervalo`.
   Una derivada que aún no se puede calcular aparece como `nan`; no es cero.
5. Solo guarda y publica cuando al menos una articulación supera el umbral de
   `0.001 rad/s`. El filtro puede omitir movimientos más lentos; se puede ajustar
   `UMBRAL_VELOCIDAD`. La diferenciación numérica puede amplificar el ruido.
6. El movimiento `joint` fija un objetivo articular con MoveIt. El lineal usa
   interpolación cartesiana. El circular aproxima una circunferencia en el plano
   XY con 32 pequeños segmentos cartesianos y mantiene la orientación. Se exige
   que MoveIt planifique prácticamente el recorrido completo antes de ejecutarlo.

En caso de que no haya velocidad publicada, hacen falta dos posiciones para
estimar una velocidad y una muestra más para estimar una aceleración. Las
primeras derivadas todavía no disponibles aparecen como `nan` en el CSV.

El registro depende de las muestras que publica el simulador; la planificación
y las pausas sin movimiento se filtran. No hay gráficos automáticos: los CSV se
pueden analizar con una hoja de cálculo o con Python.

## Entrega y comprensión

El enunciado exige un repositorio de GitHub accesible y contribuciones propias
de cada miembro mediante commits. También advierte que cada estudiante debe
comprender y defender el código. Revisad y probad el programa juntos, entendiendo
en especial las derivadas, el filtro de movimiento y cómo distingue cada CSV.
