import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QFrame, QLabel, QTextEdit, QPushButton, QComboBox, QSlider)
from PyQt6.QtCore import Qt

from config.parameters import (
    ESP_PORT_DEFAULT,
    LIDAR_PORT_DEFAULT,
    PORT_FALLBACK_OPTIONS,
    CLASS_NAMES,
    YOLO_CONFIDENCE_THRESHOLD
)

logger = logging.getLogger("SEEZY")

class MainWindow(QMainWindow):
    def __init__(self, controller=None, log_handler=None):
        super().__init__()
        self.setWindowTitle("SEEZY System Controller - Jetson Orin Nano")
        self.resize(1024, 720)
        self.setMinimumSize(900, 600)

        self.controller = controller
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        if log_handler:
            log_handler.log_signal.connect(self.append_log)

        self._init_ui()

        if self.controller:
            self.controller.state_changed.connect(self.update_status_panel)
            self.controller.queue_updated.connect(self.update_queue_display)
            self.controller.health_updated.connect(self.update_health_indicators)
            self.controller.emit_all_states()

        self.setFocus()
        logger.info("SEEZY System Controller Ready.")

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)

        upper_layout = QHBoxLayout()
        upper_layout.setSpacing(15)

        # ==========================================
        # LEFT COLUMN
        # ==========================================
        left_column = QVBoxLayout()
        left_column.setSpacing(12)

        config_frame = QFrame()
        config_frame.setStyleSheet("background-color: #252526; border-radius: 6px; padding: 10px;")
        config_layout = QHBoxLayout(config_frame)
        
        label_style = "color: #ffffff; font-weight: bold; font-size: 13px;"
        combo_style = """
            QComboBox {
                background-color: #333333; color: #ffffff; font-weight: bold;
                padding: 5px 10px; border: 1px solid #555555; border-radius: 4px;
            }
            QComboBox QAbstractItemView {
                background-color: #252526; color: #ffffff;
                selection-background-color: #007acc; selection-color: #ffffff;
            }
        """

        esp_lbl = QLabel("ESP32:")
        esp_lbl.setStyleSheet(label_style)
        config_layout.addWidget(esp_lbl)
        
        self.esp_combo = QComboBox()
        self.esp_combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.esp_combo.addItems(PORT_FALLBACK_OPTIONS)
        self.esp_combo.setCurrentText(ESP_PORT_DEFAULT)
        self.esp_combo.setStyleSheet(combo_style)
        config_layout.addWidget(self.esp_combo)
        
        lidar_lbl = QLabel("LiDAR:")
        lidar_lbl.setStyleSheet(label_style)
        config_layout.addWidget(lidar_lbl)
        
        self.lidar_combo = QComboBox()
        self.lidar_combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lidar_combo.addItems(PORT_FALLBACK_OPTIONS)
        self.lidar_combo.setCurrentText(LIDAR_PORT_DEFAULT)
        self.lidar_combo.setStyleSheet(combo_style)
        config_layout.addWidget(self.lidar_combo)
        
        self.launch_ros_btn = QPushButton("LAUNCH ROS 2")
        self.launch_ros_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.launch_ros_btn.setStyleSheet("""
            QPushButton { background-color: #007acc; color: white; font-weight: bold; font-size: 12px; padding: 6px 14px; border-radius: 4px; }
            QPushButton:hover { background-color: #005999; }
        """)
        self.launch_ros_btn.clicked.connect(self.trigger_ros_launch)
        config_layout.addWidget(self.launch_ros_btn)
        left_column.addWidget(config_frame)

        health_frame = QFrame()
        health_frame.setStyleSheet("background-color: #1e1e1e; border: 1px solid #333; border-radius: 6px; padding: 10px;")
        health_layout = QHBoxLayout(health_frame)
        
        self.health_esp = QLabel("ESP32: ⚫")
        self.health_ros = QLabel("ROS 2 Base: ⚫")
        self.health_lidar = QLabel("LiDAR: ⚫")
        self.health_vision = QLabel("YOLO Vision: ⚫")
        
        health_style = "color: #ffffff; font-size: 13px; font-weight: bold;"
        for lbl in [self.health_esp, self.health_ros, self.health_lidar, self.health_vision]:
            lbl.setStyleSheet(health_style)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            health_layout.addWidget(lbl)
        left_column.addWidget(health_frame)

        self.status_box = QFrame()
        self.status_box.setStyleSheet("background-color: #252526; border-radius: 6px; padding: 15px;")
        status_box_layout = QVBoxLayout(self.status_box)

        self.status_title = QLabel("SYSTEM STATUS")
        self.status_title.setStyleSheet("color: #888; font-size: 14px; font-weight: bold;")
        self.status_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.state_label = QLabel("SESSION: IDLE\nMODE: MANUAL\nSTATUS: READY")
        self.state_label.setStyleSheet("color: #ffaa00; font-size: 22px; font-weight: bold; padding: 10px;")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        status_box_layout.addWidget(self.status_title)
        status_box_layout.addWidget(self.state_label)
        left_column.addWidget(self.status_box)

        # ==========================================
        # RIGHT COLUMN
        # ==========================================
        right_column = QVBoxLayout()
        right_column.setSpacing(12)

        self.queue_box = QFrame()
        self.queue_box.setStyleSheet("background-color: #252526; border-radius: 6px; padding: 15px;")
        queue_layout = QVBoxLayout(self.queue_box)
        
        self.queue_title = QLabel("SHOPPING SESSION QUEUE")
        self.queue_title.setStyleSheet("color: #888; font-size: 14px; font-weight: bold;")
        self.queue_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.queue_label = QLabel("Queue: []\nTarget: None")
        self.queue_label.setStyleSheet("color: #00d2ff; font-size: 18px; font-weight: bold; padding: 10px;")
        self.queue_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        queue_layout.addWidget(self.queue_title)
        queue_layout.addWidget(self.queue_label)
        right_column.addWidget(self.queue_box)

        # Dynamic YOLO Confidence Slider
        self.conf_label = QLabel(f"YOLO Confidence: {int(YOLO_CONFIDENCE_THRESHOLD * 100)}%")
        self.conf_label.setStyleSheet("color: #cccccc; font-size: 14px; font-weight: bold;")
        
        self.conf_slider = QSlider(Qt.Orientation.Horizontal)
        self.conf_slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.conf_slider.setRange(10, 100)
        self.conf_slider.setValue(int(YOLO_CONFIDENCE_THRESHOLD * 100))
        self.conf_slider.valueChanged.connect(self._on_conf_changed)

        right_column.addWidget(self.conf_label)
        right_column.addWidget(self.conf_slider)

        # Instructions Panel (Reordered)
        self.instructions_label = QLabel(
            "<b>Controls Guide:</b><br><br>"
            "<b>[0 - 4]</b> : Select Items (Auto Mode Only)<br>"
            "<b>[5]</b>     : Route to Checkout (Auto Mode Only)<br>"
            "<b>[V]</b>     : Confirm Item Hand-off<br>"
            "<b>[C] / [X]</b>: Retry Scan / Skip & Remove Item<br>"
            "<b>[M]</b>     : Toggle Auto / Manual Mode<br>"
            "<b>[W/A/S/D]</b>: Manual Drive (Press to move, release to stop)<br>"
            "<b>[E]</b>     : Instant Motor Brake (Manual Mode Only)<br>"
            "<b>[F]</b>     : Freeze / Resume<br>"
            "<b>[SPACE]</b> : Halt (1st Press) / Reset to Manual (2nd Press)"
        )
        self.instructions_label.setStyleSheet(
            "background-color: #2d2d30; color: #cccccc; font-size: 14px; padding: 15px; border-radius: 6px;"
        )
        right_column.addWidget(self.instructions_label)

        upper_layout.addLayout(left_column, stretch=3)
        upper_layout.addLayout(right_column, stretch=2)
        main_layout.addLayout(upper_layout, stretch=3)

        # ==========================================
        # BOTTOM PANEL: Live Logs
        # ==========================================
        self.log_panel = QTextEdit()
        self.log_panel.setReadOnly(True)
        self.log_panel.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.log_panel.setStyleSheet("""
            QTextEdit {
                background-color: #121212; color: #00ff66; font-family: monospace;
                font-size: 13px; border: 1px solid #333333; border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.log_panel, stretch=2)

    def _on_conf_changed(self, value):
        self.conf_label.setText(f"YOLO Confidence: {value}%")
        if self.controller:
            self.controller.set_yolo_confidence(value / 100.0)

    def trigger_ros_launch(self):
        if not self.controller:
            return

        if self.launch_ros_btn.text() == "LAUNCH ROS 2":
            esp = self.esp_combo.currentText()
            lidar = self.lidar_combo.currentText()
            
            self.launch_ros_btn.setText("STOP ROS 2")
            self.launch_ros_btn.setStyleSheet("""
                QPushButton { background-color: #d9534f; color: white; font-weight: bold; font-size: 12px; padding: 6px 14px; border-radius: 4px; }
                QPushButton:hover { background-color: #c9302c; }
            """)
            self.controller.launch_ros2_hardware(esp, lidar)
        else:
            self.controller.stop_ros2_hardware()
            self.launch_ros_btn.setText("LAUNCH ROS 2")
            self.launch_ros_btn.setStyleSheet("""
                QPushButton { background-color: #007acc; color: white; font-weight: bold; font-size: 12px; padding: 6px 14px; border-radius: 4px; }
                QPushButton:hover { background-color: #005999; }
            """)

    def update_health_indicators(self, health_data: dict):
        def get_dot(is_healthy):
            return "🟢" if is_healthy else "🔴"
        self.health_esp.setText(f"ESP32: {get_dot(health_data.get('ESP32', False))}")
        self.health_ros.setText(f"ROS 2 Base: {get_dot(health_data.get('ROS2', False))}")
        self.health_lidar.setText(f"LiDAR: {get_dot(health_data.get('LIDAR', False))}")
        self.health_vision.setText(f"YOLO Vision: {get_dot(health_data.get('VISION', False))}")

    def append_log(self, text):
        self.log_panel.append(text)
        scrollbar = self.log_panel.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_status_panel(self, session, mode, status):
        self.state_label.setText(f"SESSION: {session}\nMODE: {mode}\nSTATUS: {status}")
        
        if status == "HALTED":
            color = "#ff3333"  # Red
        elif status == "PAUSED":
            color = "#ffaa00"  # Orange
        elif status == "DISCONNECTED":
            color = "#ff5555"  # Light Red
        else:
            color = "#ffffff"  # White
            
        self.state_label.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold; padding: 10px;")

    def update_queue_display(self, queue, target_name):
        queue_display = [f"Item {i}" for i in queue]
        self.queue_label.setText(f"Queue: {queue_display}\nTarget: {target_name}")

    def closeEvent(self, event):
        logger.info("Initiating safe shutdown...")
        if self.controller:
            self.controller.stop_system()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        is_repeat = event.isAutoRepeat()
        key = event.key()

        if not self.controller:
            return super().keyPressEvent(event)

        # Ignore auto-repeating for UI control keys so we don't spam audio/states.
        # Allow it to pass through for driving keys.
        if is_repeat and key not in (Qt.Key.Key_W, Qt.Key.Key_A, Qt.Key.Key_S, Qt.Key.Key_D):
            return

        item_map = {
            Qt.Key.Key_0: 0, 
            Qt.Key.Key_1: 1, 
            Qt.Key.Key_2: 2, 
            Qt.Key.Key_3: 3, 
            Qt.Key.Key_4: 4
        }
        
        if key in item_map:
            self.controller.handle_item_selection(item_map[key])
        elif key == Qt.Key.Key_5:
            self.controller.handle_checkout()
        elif key == Qt.Key.Key_V:
            self.controller.handle_handoff_confirm()
        elif key == Qt.Key.Key_C:
            self.controller.handle_retry_scan()
        elif key == Qt.Key.Key_X:
            self.controller.handle_skip_item()
        elif key == Qt.Key.Key_M:
            self.controller.toggle_mode()
        elif key == Qt.Key.Key_E:
            self.controller.manual_brake()
        elif key == Qt.Key.Key_F:
            self.controller.handle_f_pause()
        elif key == Qt.Key.Key_Space:
            self.controller.handle_space_halt()
        elif key in (Qt.Key.Key_W, Qt.Key.Key_A, Qt.Key.Key_S, Qt.Key.Key_D):
            direction_map = {
                Qt.Key.Key_W: "FORWARD",
                Qt.Key.Key_S: "BACKWARD",
                Qt.Key.Key_A: "LEFT",
                Qt.Key.Key_D: "RIGHT"
            }
            # Pass the auto-repeat flag to the controller
            self.controller.manual_move(direction_map[key], is_repeat=is_repeat)
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        # We ignore auto-repeating on release to prevent the motors from 
        # stuttering while the key is actively held down.
        if event.isAutoRepeat():
            return
            
        key = event.key()
        if key in (Qt.Key.Key_W, Qt.Key.Key_A, Qt.Key.Key_S, Qt.Key.Key_D):
            if self.controller:
                # Trigger silent stop command
                self.controller.manual_move("STOP")
                
        super().keyReleaseEvent(event)