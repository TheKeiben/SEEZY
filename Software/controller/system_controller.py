import os
import sys
import signal
import subprocess
import logging
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from robot.robot_controller import RobotThread
from controller.buying_session import BuyingSession
from utils.audio_manager import AudioManager

from config.parameters import (
    REQUIRED_DETECTION_STREAK,
    DETECTION_TIMEOUT_MS,
    MANUAL_SPEED_MAP,
    ROS2_SETUP_SCRIPT,
    ROS2_LAUNCH_PACKAGE,
    ROS2_LAUNCH_FILE
)

logger = logging.getLogger("SEEZY")

class SessionState(Enum):
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"

class OperatingMode(Enum):
    MANUAL = "MANUAL"
    AUTO = "AUTO"

class SystemStatus(Enum):
    DISCONNECTED = "DISCONNECTED"
    READY = "READY"
    NAVIGATING = "NAVIGATING"
    DETECTING = "DETECTING"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    PROMPT_RETRY = "PROMPT_RETRY"
    CHECKOUT = "CHECKOUT"
    PAUSED = "PAUSED"
    HALTED = "HALTED"

class SystemController(QObject):
    state_changed = pyqtSignal(str, str, str)
    queue_updated = pyqtSignal(list, str)
    health_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.session_state = SessionState.IDLE
        self.mode = OperatingMode.MANUAL
        self.status = SystemStatus.DISCONNECTED
        self.active_target_name = "None"
        self.target_item_id = None
        self.active_goal_coords = None
        self.is_detecting = False
        self.detection_streak = 0
        self.previous_status = SystemStatus.DISCONNECTED
        
        self.ros2_process = None
        self.vision_process = None

        self.subsystem_health = {
            "ESP32": False,
            "ROS2": False,
            "VISION": False,
            "LIDAR": False
        }

        self.audio = AudioManager()
        self.audio.start()
        
        msg = "System Initialized. Status: Disconnected. Please configure ports."
        logger.info(f"[Controller] {msg}")
        self.audio.speak(msg)

        self.robot_thread = RobotThread()
        self.robot_thread.detection_signal.connect(self._handle_raw_detection)
        self.robot_thread.navigation_done_signal.connect(self._handle_nav_completion)
        self.robot_thread.telemetry_signal.connect(self._handle_telemetry_update)
        self.robot_thread.obstacle_signal.connect(self._handle_obstacle)
        self.robot_thread.start()

        self.detection_timer = QTimer(self)
        self.detection_timer.setSingleShot(True)
        self.detection_timer.timeout.connect(self._handle_detection_timeout)

        self.buying_session = BuyingSession()
        self._wire_session_signals()

    def launch_ros2_hardware(self, esp_port: str, lidar_port: str):
        if self.ros2_process is not None: return
        
        msg = "Launching robot hardware nodes. Awaiting telemetry."
        logger.info(f"[Controller] {msg} -> ESP32: {esp_port} | LiDAR: {lidar_port}")
        self.audio.speak(msg)
        
        bash_cmd = (
            f"source {ROS2_SETUP_SCRIPT} && "
            f"ros2 launch {ROS2_LAUNCH_PACKAGE} {ROS2_LAUNCH_FILE} "
            f"esp_port:={esp_port} lidar_port:={lidar_port}"
        )
        try:
            self.ros2_process = subprocess.Popen(bash_cmd, shell=True, executable='/bin/bash', preexec_fn=os.setsid)
        except Exception as e:
            logger.error(f"Failed to launch ROS 2 stack: {e}")

        vision_script = os.path.join(os.path.dirname(__file__), "..", "perception", "vision_node.py")
        try:
            self.vision_process = subprocess.Popen([sys.executable, vision_script], preexec_fn=os.setsid)
        except Exception as e:
            logger.error(f"Failed to launch Vision Node: {e}")

    def stop_ros2_hardware(self):
        self.detection_timer.stop()
        if self.ros2_process:
            try: os.killpg(os.getpgid(self.ros2_process.pid), signal.SIGTERM)
            except Exception: pass
            self.ros2_process = None

        if self.vision_process:
            try: os.killpg(os.getpgid(self.vision_process.pid), signal.SIGTERM)
            except Exception: pass
            self.vision_process = None
        
        self.subsystem_health = {"ESP32": False, "ROS2": False, "VISION": False, "LIDAR": False}
        self.status = SystemStatus.DISCONNECTED
        self.previous_status = SystemStatus.DISCONNECTED
        self.emit_all_states()

    def _handle_telemetry_update(self, health_data: dict):
        self.subsystem_health = health_data
        if self.subsystem_health.get("ROS2", False) and self.status == SystemStatus.DISCONNECTED:
            self.status = SystemStatus.READY
            self.previous_status = SystemStatus.READY
            msg = "Robot hardware online. System Ready."
            logger.info(f"[Controller] {msg}")
            self.audio.speak(msg)
            
        elif not self.subsystem_health.get("ROS2", False) and self.status not in (SystemStatus.DISCONNECTED, SystemStatus.HALTED, SystemStatus.PAUSED):
            self.previous_status = self.status
            self.status = SystemStatus.DISCONNECTED
            msg = "Hardware connection lost."
            logger.warning(f"[Controller] {msg}")
            self.audio.speak(msg)
        self.emit_all_states()

    def _wire_session_signals(self):
        self.buying_session.session_started.connect(self._on_session_start)
        self.buying_session.navigating_to_item.connect(self._on_navigating_to_item)
        self.buying_session.detection_requested.connect(self._on_detection_requested)
        self.buying_session.item_completed.connect(self._on_item_completed)
        self.buying_session.navigating_to_checkout.connect(self._on_navigating_to_checkout)
        self.buying_session.session_finished.connect(self._on_session_finished)
        self.buying_session.queue_completed.connect(self._on_queue_completed)

    def _on_queue_completed(self):
        self.session_state = SessionState.IDLE
        self.status = SystemStatus.READY
        self.active_target_name = "None"
        msg = "Queue finished. Ready for more items or checkout."
        logger.info(f"[Controller] {msg}")
        self.audio.speak(msg)
        self.emit_all_states()

    def emit_all_states(self):
        self.state_changed.emit(self.session_state.value, self.mode.value, self.status.value)
        self.queue_updated.emit(self.buying_session.queue, self.active_target_name)
        self.health_updated.emit(self.subsystem_health)

    def _handle_raw_detection(self, payload: dict):
        if not self.is_detecting or self.status != SystemStatus.DETECTING:
            return

        det_id = payload.get("class_id")
        confidence = payload.get("confidence", 0.0)

        if det_id == self.target_item_id:
            self.detection_streak += 1
            if self.detection_streak >= REQUIRED_DETECTION_STREAK:
                self.detection_timer.stop()
                self.is_detecting = False
                matched_id = self.target_item_id
                self.target_item_id = None
                self.detection_streak = 0
                
                self.status = SystemStatus.WAITING_FOR_USER
                # We pass the exact confidence to the BuyingSession so it can log it accurately
                self.buying_session.on_item_detected(matched_id, True, confidence)
                self.emit_all_states()
        else:
            self.detection_streak = 0

    def _handle_detection_timeout(self):
        if self.status == SystemStatus.DETECTING and self.is_detecting:
            self.is_detecting = False
            self.status = SystemStatus.PROMPT_RETRY
            msg = "Item not detected. Press C to retry, or X to skip."
            logger.warning(f"[Controller] {msg}")
            self.audio.speak(msg)
            self.emit_all_states()
            
    def _handle_obstacle(self):
        if self.status in (SystemStatus.NAVIGATING, SystemStatus.CHECKOUT):
            msg = "Obstacle detected, navigating around."
            logger.warning(f"[Nav2] {msg}")
            self.audio.speak(msg)

    def set_yolo_confidence(self, conf: float):
        self.robot_thread.set_confidence(conf)

    def handle_handoff_confirm(self):
        if self.status == SystemStatus.WAITING_FOR_USER:
            msg = "Item secured. Resuming route."
            logger.info(f"[Controller] {msg}")
            self.audio.speak(msg)
            self.buying_session.advance_queue()

    def handle_retry_scan(self):
        if self.status == SystemStatus.PROMPT_RETRY:
            msg = f"Retrying scan for {self.active_target_name}..."
            logger.info(f"[Controller] {msg}")
            self.audio.speak(msg)
            item_id = self.buying_session.queue[0]
            self._on_detection_requested(item_id, self.active_target_name)

    def handle_skip_item(self):
        if self.status == SystemStatus.PROMPT_RETRY:
            msg = "Item skipped and removed from queue."
            logger.info(f"[Controller] {msg}")
            self.audio.speak(msg)
            self.buying_session.advance_queue()

    def handle_space_halt(self):
        """First press: Stop everything. Second press: Hard reset system to IDLE/MANUAL."""
        if self.status == SystemStatus.HALTED:
            msg = "System Resetting to Manual Mode."
            logger.info(f"[Controller] {msg}")
            self.audio.speak(msg)
            
            self.session_state = SessionState.IDLE
            self.mode = OperatingMode.MANUAL
            self.status = SystemStatus.READY
            self.active_target_name = "None"
            self.active_goal_coords = None
            self.buying_session.is_active = False
            self.buying_session.queue.clear()
            self.is_detecting = False
            self.detection_timer.stop()
            self.robot_thread.publish_velocity(0.0, 0.0)
            self.robot_thread.cancel_navigation()
            self.emit_all_states()
        else:
            msg = "Emergency Halt. Press Space again to reset."
            logger.warning(f"[Controller] {msg}")
            self.audio.speak(msg)
            
            self.previous_status = self.status
            self.status = SystemStatus.HALTED
            self.active_goal_coords = None  # Crucial: Wipes coordinates so it CANNOT be resumed
            self.robot_thread.publish_velocity(0.0, 0.0)
            
            if self.previous_status in (SystemStatus.NAVIGATING, SystemStatus.CHECKOUT):
                self.robot_thread.cancel_navigation()
            if self.is_detecting:
                self.detection_timer.stop()
                
            self.emit_all_states()

    def handle_f_pause(self):
        """True Freeze: Freezes current state, safely saves target coordinates, and resumes perfectly on second press."""
        if self.status in (SystemStatus.DISCONNECTED, SystemStatus.HALTED): return
        
        if self.status == SystemStatus.PAUSED:
            msg = "System Resumed."
            logger.info(f"[Controller] {msg}")
            self.audio.speak(msg)
            
            self.status = self.previous_status
            
            if self.status in (SystemStatus.NAVIGATING, SystemStatus.CHECKOUT) and self.active_goal_coords:
                self.robot_thread.navigate_to(*self.active_goal_coords)
            elif self.status == SystemStatus.DETECTING and self.is_detecting:
                self.detection_timer.start(DETECTION_TIMEOUT_MS)
                
            self.emit_all_states()
        else:
            msg = "System Paused."
            logger.info(f"[Controller] {msg}")
            self.audio.speak(msg)
            
            self.previous_status = self.status
            self.status = SystemStatus.PAUSED
            
            self.robot_thread.publish_velocity(0.0, 0.0)
            if self.previous_status in (SystemStatus.NAVIGATING, SystemStatus.CHECKOUT):
                self.robot_thread.cancel_navigation()
            elif self.is_detecting:
                self.detection_timer.stop()
                
            self.emit_all_states()

    def manual_brake(self):
        if self.status in (SystemStatus.DISCONNECTED, SystemStatus.HALTED, SystemStatus.PAUSED): return
        
        if self.mode != OperatingMode.MANUAL:
            msg = "Cannot brake manually in Auto mode."
            logger.warning(f"[Controller] {msg}")
            self.audio.speak(msg)
            return
            
        self.robot_thread.publish_velocity(0.0, 0.0)
        logger.info("[Controller] Instant motor brake applied.")

    def manual_move(self, direction: str, is_repeat: bool = False):
        if self.status in (SystemStatus.DISCONNECTED, SystemStatus.HALTED, SystemStatus.PAUSED): return
        
        if self.mode != OperatingMode.MANUAL:
            if direction != "STOP" and not is_repeat:
                msg = "Cannot drive manually in Auto mode."
                logger.warning(f"[Controller] {msg}")
                self.audio.speak(msg)
            return
            
        if direction == "STOP":
            self.robot_thread.publish_velocity(0.0, 0.0)
        else:
            lin, ang = MANUAL_SPEED_MAP.get(direction, (0.0, 0.0))
            self.robot_thread.publish_velocity(lin, ang)
            
            # Smart logging: Only log the initial press, skip during auto-repeat
            if not is_repeat:
                logger.info(f"[Controller] Manual Drive: {direction}")

    def handle_item_selection(self, class_id: int):
        if self.status in (SystemStatus.DISCONNECTED, SystemStatus.HALTED, SystemStatus.PAUSED): return
        
        if self.mode != OperatingMode.AUTO:
            msg = "Cannot select items in Manual mode."
            logger.warning(f"[Controller] {msg}")
            self.audio.speak(msg)
            return
        
        if self.buying_session.add_item(class_id):
            msg = f"Item {class_id} added to queue."
            logger.info(f"[Controller] {msg}")
            self.audio.speak(msg)
            if self.session_state == SessionState.IDLE:
                self.session_state = SessionState.ACTIVE
                self.buying_session.start_session()
            else:
                self.emit_all_states()

    def handle_checkout(self):
        if self.status in (SystemStatus.DISCONNECTED, SystemStatus.HALTED, SystemStatus.PAUSED): return
        
        if self.mode != OperatingMode.AUTO:
            msg = "Cannot select checkout in Manual mode."
            logger.warning(f"[Controller] {msg}")
            self.audio.speak(msg)
            return
            
        self.session_state = SessionState.ACTIVE
        self.buying_session.is_active = True
        self.buying_session.navigate_checkout()

    def toggle_mode(self):
        if self.status in (SystemStatus.DISCONNECTED, SystemStatus.HALTED, SystemStatus.PAUSED): return
        
        if self.mode == OperatingMode.MANUAL:
            self.mode = OperatingMode.AUTO
            msg = "Auto mode activated."
            logger.info(f"[Controller] {msg}")
            self.audio.speak(msg)
        else:
            self.mode = OperatingMode.MANUAL
            msg = "Manual mode activated."
            logger.info(f"[Controller] {msg}")
            self.audio.speak(msg)
            
            if self.session_state == SessionState.ACTIVE:
                self.buying_session.is_active = False
                self.buying_session.queue.clear()
                self.session_state = SessionState.IDLE
                self.status = SystemStatus.READY
                self.active_target_name = "None"
                self.active_goal_coords = None
                self.robot_thread.publish_velocity(0.0, 0.0)
                self.robot_thread.cancel_navigation()
                if self.is_detecting:
                    self.detection_timer.stop()
                    self.is_detecting = False
        self.emit_all_states()

    def _handle_nav_completion(self, success: bool):
        if success:
            msg = f"Arrived at {self.active_target_name}."
            logger.info(f"[Controller] {msg}")
            self.audio.speak(msg)
            if self.status == SystemStatus.CHECKOUT:
                self.buying_session.complete_checkout()
            elif self.status == SystemStatus.NAVIGATING:
                self.buying_session.on_navigation_arrived()
        else:
            if self.status in (SystemStatus.HALTED, SystemStatus.READY, SystemStatus.PAUSED): return
            msg = "Navigation Error. Shopping session aborted."
            logger.error(f"[Controller] {msg}")
            self.audio.speak(msg)
            self.buying_session.is_active = False
            self.buying_session.queue.clear()
            self.session_state = SessionState.IDLE
            self.status = SystemStatus.READY
            self.active_goal_coords = None
            self.emit_all_states()

    def _on_session_start(self, queue):
        self.session_state = SessionState.ACTIVE
        self.status = SystemStatus.NAVIGATING
        self.emit_all_states()

    def _on_navigating_to_item(self, item_id, item_name, coords):
        self.status = SystemStatus.NAVIGATING
        self.active_target_name = item_name
        self.active_goal_coords = (coords['x'], coords['y'], coords['theta'])
        
        msg = f"Navigating to {item_name}."
        logger.info(f"[Controller] {msg}")
        self.audio.speak(msg)
        self.emit_all_states()
        self.robot_thread.navigate_to(*self.active_goal_coords)

    def _on_detection_requested(self, item_id, item_name):
        self.status = SystemStatus.DETECTING
        self.target_item_id = item_id
        self.is_detecting = True
        self.detection_streak = 0
        self.active_goal_coords = None 
        
        msg = f"Scanning for {item_name}."
        logger.info(f"[Controller] {msg}")
        self.audio.speak(msg)
        self.detection_timer.start(DETECTION_TIMEOUT_MS)
        self.emit_all_states()

    def _on_item_completed(self, item_id, item_name):
        msg = "Item found. Please place it in the basket and press V to continue."
        logger.info(f"[Controller] {msg}")
        self.audio.speak(msg)

    def _on_navigating_to_checkout(self, checkout_coords):
        self.status = SystemStatus.CHECKOUT
        self.active_target_name = "Checkout Counter"
        self.active_goal_coords = (checkout_coords['x'], checkout_coords['y'], checkout_coords['theta'])
        
        msg = "Navigating to checkout."
        logger.info(f"[Controller] {msg}")
        self.audio.speak(msg)
        self.emit_all_states()
        self.robot_thread.navigate_to(*self.active_goal_coords)

    def _on_session_finished(self):
        self.session_state = SessionState.IDLE
        self.status = SystemStatus.READY
        self.active_target_name = "None"
        self.active_goal_coords = None
        msg = "Shopping session completed. Thank you."
        logger.info(f"[Controller] {msg}")
        self.audio.speak(msg)
        self.emit_all_states()

    def stop_system(self):
        msg = "Shutting down system."
        logger.info(f"[Controller] {msg}")
        self.audio.speak(msg)
        self.stop_ros2_hardware()
        self.robot_thread.stop()
        self.audio.stop()