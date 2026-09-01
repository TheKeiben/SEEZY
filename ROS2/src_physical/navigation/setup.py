from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'navigation'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        # 1. Standard ROS 2 Package Files
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),

        # 2. Launch Files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        # 3. Config Files (CRITICAL FIX: Now includes both YAML params and XML Behavior Trees)
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml') + glob('config/*.xml')),
        # 4. Map Files
        (os.path.join('share', package_name, 'maps'), glob('maps/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,

    # 5. Package Metadata (Aligned with package.xml)
    maintainer='SEEZY',
    maintainer_email='SEEZY@gmail.com',
    description='Navigation package for the SEEZY robot utilizing Nav2 planners, controllers, and behavior trees.',
    license='Apache 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # No pure python nodes to run via 'ros2 run' in this package
        ],
    },
)
