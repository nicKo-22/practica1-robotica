from setuptools import find_packages, setup

package_name = 'pruebas'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Estudiante',
    maintainer_email='estudiante@example.com',
    description='Ejemplos de control, publicación y suscripción del laboratorio',
    license='Apache-2.0',
)
