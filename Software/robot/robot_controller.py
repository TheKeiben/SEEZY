import math
import json
import logging
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import Twist
from std_msgs.msg import String, Int32, Float32
from std_srvs.srv import Trigger
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from nav2_msgs.action import NavigateToPose
from PyQt6.QtCore import QThread, pyqtSignal

from config.parameters import (
    TOPIC_CMD_VEL,
    TOPIC_SCAN,
    TOPIC_ODOM,
    TOPIC_ENCODER_LEFT,
    TOPIC_VISION_DETECTIONS,
    TOPIC_VISION_HEALTH,
    TOPIC_SET_CONFIDENCE,
    SERVICE_RESET_ESP,
    ACTION_NAVIGATE_TO_POSE,
    TELEMETRY_TIMEOUT_SEC,
    HEALTH_TIMER_FREQ_HZ,
    NAV2_SERVER_TIMEOUT_SEC
)

logger = logging.getLogger("SEEZY")

class SeezyCoreNode(Node):
    def __init__(self, detection_callback, nav_complete_callback, health_callback, obstacle_callback):
        super().__init__('seezy_core_node')
        
        self.on_detection_received = detection_callback
        self.on_nav_complete = nav_complete_callback
        self.on_health_update = health_callback
        self.on_obstacle_detected = obstacle_callback

        # Publishers & Subscribers
        self.cmd_vel_pub = self.create_publisher(Twist, TOPIC_CMD_VEL, 10)
        self.conf_pub = self.create_publisher(Float32, TOPIC_SET_CONFIDENCE, 10)
        
        self.detection_sub = self.create_subscription(String, TOPIC_VISION_DETECTIONS, self._detection_callback, 10)
        self.lidar_sub = self.create_subscription(LaserScan, TOPIC_SCAN, self._lidar_callback, 10)
        self.odom_sub = self.create_subscription(Odometry, TOPIC_ODOM, self._odom_callback, 10)
        self.esp_sub = self.create_subscription(Int32, TOPIC_ENCODER_LEFT, self._esp_callback, 10)
        self.vision_health_sub = self.create_subscription(String, TOPIC_VISION_HEALTH, self._vision_health_callback, 10)
        
        self.reset_client = self.create_client(Trigger, SERVICE_RESET_ESP)
        
        self.nav_client = ActionClient(self, NavigateToPose, ACTION_NAVIGATE_TO_POSE)
        self.active_goal_handle = None
        self.recovery_count = 0
        
        self.health_state = {"ESP32": False, "ROS2": False, "LIDAR": False, "VISION": False}
        self.last_esp_time = 0.0
        self.last_lidar_time = 0.0
        self.last_odom_time = 0.0
        self.last_vision_time = 0.0

        timer_period = 1.0 / HEALTH_TIMER_FREQ_HZ
        self.health_timer = self.create_timer(timer_period, self._check_telemetry_heartbeats)
        logger.info("[ROS 2] SeezyCoreNode Initialized.")

    def reset_esp32(self):
        if not self.reset_client.wait_for_service(timeout_sec=2.0):
            logger.warning(f"[ESP32 Reset] Service {SERVICE_RESET_ESP} unavailable.")
            return
        req = Trigger.Request()
        self.reset_client.call_async(req)
        logger.info("[ESP32 Reset] Software reset command transmitted to ESP32.")

    def publish_velocity(self, linear_x: float, angular_z: float):
        msg = Twist()
        msg.linear.x = float(linear_x)
        msg.angular.z = float(angular_z)
        self.cmd_vel_pub.publish(msg)
        
    def set_confidence(self, conf: float):
        msg = Float32()
        msg.data = float(conf)
        self.conf_pub.publish(msg)

    def _esp_callback(self, msg: Int32):
        self.last_esp_time = self.get_clock().now().nanoseconds / 1e9

    def _vision_health_callback(self, msg: String):
        self.last_vision_time = self.get_clock().now().nanoseconds / 1e9

    def _detection_callback(self, msg: String):
        try:
            data = json.loads(msg.data)
            self.on_detection_received(data)
        except Exception as e:
            logger.error(f"[Perception] JSON parse error: {e}")

    def _lidar_callback(self, msg: LaserScan):
        self.last_lidar_time = self.get_clock().now().nanoseconds / 1e9

    def _odom_callback(self, msg: Odometry):
        self.last_odom_time = self.get_clock().now().nanoseconds / 1e9

    def _check_telemetry_heartbeats(self):
        now = self.get_clock().now().nanoseconds / 1e9
        esp_alive = (now - self.last_esp_time) < TELEMETRY_TIMEOUT_SEC
        ros_alive = (now - self.last_odom_time) < TELEMETRY_TIMEOUT_SEC
        lidar_alive = (now - self.last_lidar_time) < TELEMETRY_TIMEOUT_SEC
        vision_alive = (now - self.last_vision_time) < TELEMETRY_TIMEOUT_SEC

        if (esp_alive != self.health_state["ESP32"] or
            ros_alive != self.health_state["ROS2"] or 
            lidar_alive != self.health_state["LIDAR"] or 
            vision_alive != self.health_state["VISION"]):
            
            self.health_state["ESP32"] = esp_alive
            self.health_state["ROS2"] = ros_alive
            self.health_state["LIDAR"] = lidar_alive
            self.health_state["VISION"] = vision_alive
            self.on_health_update(self.health_state.copy())

    def send_nav_goal(self, x: float, y: float, theta: float):
        if not self.nav_client.wait_for_server(timeout_sec=NAV2_SERVER_TIMEOUT_SEC):
            logger.error(f"[Nav2] Action server {ACTION_NAVIGATE_TO_POSE} not available!")
            self.on_nav_complete(False)
            return

        self.recovery_count = 0
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        
        goal_msg.pose.pose.position.x = float(x)
        goal_msg.pose.pose.position.y = float(y)
        goal_msg.pose.pose.position.z = 0.0
        
        goal_msg.pose.pose.orientation.x = 0.0
        goal_msg.pose.pose.orientation.y = 0.0
        goal_msg.pose.pose.orientation.z = math.sin(theta / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(theta / 2.0)

        logger.info(f"[Nav2] Sending Goal -> X: {x}, Y: {y}, Theta: {theta}")
        # Added feedback_callback
        self.send_goal_future = self.nav_client.send_goal_async(goal_msg, feedback_callback=self._nav_feedback_callback)
        self.send_goal_future.add_done_callback(self._goal_response_callback)

    def _nav_feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        if hasattr(feedback, 'number_of_recoveries') and feedback.number_of_recoveries > self.recovery_count:
            self.recovery_count = feedback.number_of_recoveries
            self.on_obstacle_detected()

    def _goal_response_callback(self, future):
        self.active_goal_handle = future.result()
        if not self.active_goal_handle.accepted:
            logger.warning("[Nav2] Goal rejected by robot.")
            self.active_goal_handle = None
            self.on_nav_complete(False)
            return

        logger.info("[Nav2] Goal accepted! Robot is moving...")
        self.get_result_future = self.active_goal_handle.get_result_async()
        self.get_result_future.add_done_callback(self._get_result_callback)

    def _get_result_callback(self, future):
        status = future.result().status
        self.active_goal_handle = None
        success = (status == 4)
        if success:
            logger.info("[Nav2] Robot reached destination pose.")
        else:
            logger.warning(f"[Nav2] Navigation ended with status code: {status}")
        self.on_nav_complete(success)

    def cancel_active_goal(self):
        if self.active_goal_handle is not None:
            logger.info("[Nav2] Canceling active trajectory goal...")
            self.active_goal_handle.cancel_goal_async()
            self.active_goal_handle = None

class RobotThread(QThread):
    detection_signal = pyqtSignal(dict)
    navigation_done_signal = pyqtSignal(bool)
    telemetry_signal = pyqtSignal(dict)
    obstacle_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.node = None

    def run(self):
        self.node = SeezyCoreNode(self._emit_detection, self._emit_nav_done, self._emit_telemetry, self._emit_obstacle)
        rclpy.spin(self.node)

    def _emit_detection(self, data: dict):
        self.detection_signal.emit(data)

    def _emit_nav_done(self, success: bool):
        self.navigation_done_signal.emit(success)

    def _emit_telemetry(self, health_data: dict):
        self.telemetry_signal.emit(health_data)
        
    def _emit_obstacle(self):
        self.obstacle_signal.emit()

    def reset_esp32(self):
        if self.node:
            self.node.reset_esp32()

    def publish_velocity(self, lin: float, ang: float):
        if self.node:
            self.node.publish_velocity(lin, ang)
            
    def set_confidence(self, conf: float):
        if self.node:
            self.node.set_confidence(conf)

    def navigate_to(self, x: float, y: float, theta: float):
        if self.node:
            self.node.send_nav_goal(x, y, theta)

    def cancel_navigation(self):
        if self.node:
            self.node.cancel_active_goal()

    def stop(self):
        if self.node:
            self.node.destroy_node()
        self.quit()