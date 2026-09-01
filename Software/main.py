import sys
import rclpy
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from controller.system_controller import SystemController
from utils.logging_config import setup_logger

def main():
    # 1. Setup logging system
    logger, qt_log_handler = setup_logger()
    logger.info("Booting SEEZY Controller on Jetson Orin Nano...")

    # Initialize ROS 2 globally
    rclpy.init(args=sys.argv)

    # 2. Start Application
    app = QApplication(sys.argv)

    # 3. Create controller and pass directly to UI
    controller = SystemController()
    window = MainWindow(controller=controller, log_handler=qt_log_handler)
    window.show()

    # 4. Run event loop
    exit_code = app.exec()


    # Clean up ROS 2 threads on exit
    controller.stop_system()
    rclpy.shutdown()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()