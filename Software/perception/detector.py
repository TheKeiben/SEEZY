import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from PyQt6.QtCore import QThread, pyqtSignal
import json
import logging

logger = logging.getLogger("SEEZY")

class YoloSubscriberNode(Node):
    """ROS 2 Node that listens to the vision node's output."""
    def __init__(self, callback):
        super().__init__('seezy_detector_ui_bridge')
        # Subscribes to the detections topic
        self.subscription = self.create_subscription(
            String, 
            '/seezy/detections', 
            self.listener_callback, 
            10
        )
        self.callback = callback

    def listener_callback(self, msg):
        self.callback(msg.data)

class YoloDetectorThread(QThread):
    # Emits (item_id, success_boolean) when the item is found
    detection_result = pyqtSignal(int, bool)

    def __init__(self):
        super().__init__()
        self.active = False
        self.target_item_id = None
        self.node = None
        
        # Dictionary mapping your 5 classes
        self.class_names = {
            0: "milk_3p_tnuva",
            1: "ketchup_heinz",
            2: "bamba_osem",
            3: "cafe_names_elit",
            4: "toothpaste_colgate"
        }

    def start_detection(self, item_id: int):
        """Triggers the UI to start listening for a specific item."""
        self.target_item_id = item_id
        self.active = True
        target_name = self.class_names.get(item_id, "Unknown")
        logger.info(f"[Perception] Listening to vision node for: {target_name}...")

    def stop_detection(self):
        """Halts the listening state."""
        self.active = False

    def run(self):
        """Spins the ROS 2 subscriber in the background."""
        self.node = YoloSubscriberNode(self.process_detection)
        rclpy.spin(self.node)

    def process_detection(self, data_str):
        """Parses incoming detections from the vision node."""
        if not self.active:
            return
            
        try:
            # Expecting JSON like: {"class_id": 1, "confidence": 0.85}
            payload = json.loads(data_str)
            det_id = payload.get("class_id")
            
            if det_id == self.target_item_id:
                target_name = self.class_names.get(self.target_item_id)
                logger.info(f"[Perception] SUCCESS: {target_name} detected via ROS 2!")
                self.detection_result.emit(self.target_item_id, True)
                self.active = False  # Stop listening once found
                
        except Exception as e:
            logger.error(f"[Perception] Error parsing vision data: {e}")

    def stop(self):
        """Cleans up the node on shutdown."""
        if self.node:
            self.node.destroy_node()
        self.quit()