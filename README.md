# Práctica 1: registro de datos cinemáticos del UR3e

Esta práctica utiliza ROS 2 Jazzy y MoveIt 2 para mover un robot UR3e **en simulación** y registrar la posición, velocidad y aceleración de sus seis articulaciones. El programa lleva el robot a una posición inicial y ejecuta tres trayectorias: articular, lineal y circular. Los datos de cada una se guardan en un archivo CSV.

El entorno se ejecuta en Docker y el simulador se visualiza en el navegador mediante un escritorio remoto. No es necesario instalar ROS 2 directamente en el equipo.

## Requisitos

- Git, para clonar el repositorio.
- Docker y Docker Compose v2 en funcionamiento. En Windows, instala y abre [Docker Desktop](https://www.docker.com/products/docker-desktop/); necesita WSL 2.
- Conexión a Internet para descargar y construir la imagen la primera vez.
- Un navegador web para ver RViz y el robot simulado.

En Linux puedes comprobar que Docker y Compose están disponibles con `docker --version` y `docker compose version`. El usuario debe tener permisos para ejecutar Docker. En Windows, espera a que Docker Desktop indique que está en marcha antes de continuar.

## 1. Descargar el repositorio

En una terminal de **Linux**, por ejemplo desde tu carpeta personal:

```bash
cd ~
git clone https://github.com/nicKo-22/practica1-robotica.git
cd ~/practica1-robotica
```

En **Windows**, abre PowerShell y ejecuta:

```powershell
git clone https://github.com/nicKo-22/practica1-robotica.git
cd .\practica1-robotica
```

Si ya tienes el repositorio descargado, entra en su carpeta en lugar de clonarlo de nuevo. En Linux, sustituye `~/practica1-robotica` por la ruta real si lo guardaste en otro lugar. Comprueba que en esa carpeta están `lab.sh`, `lab.bat` y `ros_workspace/`.

## 2. Iniciar el entorno y compilar

Los comandos de esta sección se ejecutan en el **equipo anfitrión**, desde la raíz del repositorio.

En **Linux**:

```bash
cd ~/practica1-robotica
bash lab.sh iniciar
bash lab.sh compilar
```

En **Windows**, desde PowerShell:

```powershell
.\lab.bat iniciar
.\lab.bat compilar
```

La primera ejecución descarga y construye la imagen, por lo que puede tardar varios minutos. El inicio compila el espacio de trabajo si aún no existe una instalación; el comando `compilar` asegura que se incluyan los paquetes actuales de la práctica. Repite la compilación cuando añadas paquetes o modifiques interfaces.

El escritorio debería abrirse automáticamente. Si no lo hace, entra en [http://localhost:6081](http://localhost:6081) y usa la contraseña **`laboratorio`**. RViz aparecerá en este escritorio cuando se lance la simulación.

## 3. Lanzar la simulación

Desde la raíz del repositorio, en una terminal del **equipo anfitrión**:

**Linux:**

```bash
cd ~/practica1-robotica
bash lab.sh sim 203
```

**Windows:**

```powershell
.\lab.bat sim 203
```

Mantén esta terminal abierta. Espera a que aparezca el robot en RViz y a que MoveIt termine de arrancar antes de ejecutar la práctica. La práctica está configurada para una escena de **un solo robot**, como la simulación del 203.

## 4. Ejecutar la práctica

Abre **otra terminal en el equipo anfitrión**, entra en la raíz del repositorio y abre una terminal dentro del contenedor:

**Linux:**

```bash
cd ~/practica1-robotica
bash lab.sh terminal
```

**Windows:**

```powershell
cd ruta\a\practica1-robotica
.\lab.bat terminal
```

En Windows, sustituye `ruta\a\practica1-robotica` por la ruta donde clonaste el proyecto. A partir de aquí estás **dentro del contenedor Linux**. Ejecuta:

```bash
source /opt/ros/jazzy/setup.bash
cd /home/laboratorio/ros_workspace
source install/setup.bash
ros2 run practica_1 practica
```

La ruta `/home/laboratorio/ros_workspace` pertenece al contenedor y corresponde a la carpeta `ros_workspace` del repositorio en tu equipo. La activación con `source` se realiza en cada terminal del contenedor donde quieras usar los paquetes del espacio de trabajo.

El programa mueve el robot a la posición inicial sin guardar muestras y después ejecuta y registra las tres trayectorias. La terminal informa del progreso y, al finalizar, de la ruta de los datos. Si la planificación o la ejecución falla, el programa se detiene y los CSV ya creados pueden quedar vacíos o incompletos.

## 5. Consultar los resultados

Al ejecutar el programa desde `/home/laboratorio/ros_workspace`, se crea una carpeta con fecha y hora por cada ejecución:

```text
ros_workspace/datos_practica_1/<fecha_hora>/
├── joint.csv
├── lineal.csv
└── circular.csv
```

Puedes acceder a esa carpeta directamente desde el explorador de archivos de tu equipo, dentro del repositorio. Cada fila del CSV corresponde a una articulación y contiene segundos, nanosegundos, nombre, posición en radianes, velocidad en rad/s y aceleración en rad/s². Las muestras sin movimiento se filtran; un valor `nan` indica que todavía no se ha podido calcular una derivada.

Para indicar otro directorio de salida, ejecuta dentro del contenedor:

```bash
ros2 run practica_1 practica --ros-args -p directorio_salida:=/home/laboratorio/ros_workspace/datos_practica_1
```

Puedes consultar también los datos publicados en el topic `/datos_cinematicos`. Abre otra terminal del contenedor **antes de ejecutar la práctica** y ejecuta:

```bash
source /opt/ros/jazzy/setup.bash
cd /home/laboratorio/ros_workspace
source install/setup.bash
ros2 topic echo /datos_cinematicos
```

## 6. Detener el entorno

Cuando termine la práctica, detén la simulación con `Ctrl+C` en la terminal donde ejecutaste `sim 203`. Sal de las terminales del contenedor con `exit` y, desde la raíz del repositorio en el equipo anfitrión, para el contenedor:

**Linux:**

```bash
bash lab.sh parar
```

**Windows:**

```powershell
.\lab.bat parar
```

Los datos guardados en `ros_workspace` permanecen en el equipo anfitrión. Para volver a trabajar, inicia el entorno de nuevo y repite los pasos de simulación y ejecución.

## Estructura del proyecto

```text
.
├── lab.sh / lab.bat / lab.ps1       # Inicio, compilación y acceso al entorno
├── docker-compose.yml               # Configuración de los contenedores
├── dockerfiles/                     # Imágenes de Docker
└── ros_workspace/
    └── src/
        ├── PRACTICA1/
        │   ├── practica_1/           # Nodo, trayectorias y registro
        │   └── practica_1_interfaces/  # Mensaje DatosCinematicos
        ├── launcher_robots_lab_robotica/ # Lanzadores y configuración del robot
        └── rg2_driver/              # Controlador de la pinza
```

Dentro de `practica_1/practica_1/`, `tarea_1_suscriptor.py` recibe `/joint_states`, `tarea_2_trayectorias.py` define los movimientos y `tarea_3_procesamiento.py` calcula y guarda los datos. [La documentación de la práctica](ros_workspace/src/PRACTICA1/practica_1/README.md) explica el procesamiento y el mensaje personalizado con más detalle.

## Problemas frecuentes

- **Docker no está en ejecución:** abre Docker Desktop o inicia el servicio Docker en Linux y espera a que esté listo.
- **Permiso denegado al usar Docker en Linux:** configura el acceso de tu usuario al servicio Docker y vuelve a iniciar sesión. Si falla la escritura en `ros_workspace`, comprueba los permisos de esa carpeta en el anfitrión; el usuario del contenedor tiene UID 1000.
- **La página del escritorio no carga:** espera unos segundos y vuelve a abrir [localhost:6081](http://localhost:6081). Comprueba también que el puerto 6081 no esté ocupado.
- **No se encuentra `practica_1` o su interfaz:** ejecuta el comando `compilar` del paso 2, abre una nueva terminal del contenedor y vuelve a ejecutar los dos comandos `source` del paso 4.
- **MoveIt no responde o no se reciben articulaciones:** comprueba que la simulación siga ejecutándose y que haya terminado de arrancar antes de iniciar la práctica.
- **Un movimiento falla o un CSV está incompleto:** revisa el error de la terminal y vuelve a ejecutar la práctica con la simulación activa. Los desplazamientos se definen en `tarea_2_trayectorias.py` y `configuracion.py`.

El repositorio incluye también lanzadores para robots reales y escenas con dos robots, pero esta práctica está preparada para la simulación individual descrita arriba.
