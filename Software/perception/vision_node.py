#!/usr/bin/env python3
import os
import sys
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32
from sensor_msgs.msg import Image
import cv2
import json
import threading
from ultralytics import YOLO

# Ensure parent directory is in sys.path for direct standalone execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.parameters import (
    MODEL_FILENAME,
    CAMERA_DEVICE,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_FPS,
    YOLO_CONFIDENCE_THRESHOLD,
    TOPIC_VISION_DETECTIONS,
    TOPIC_VISION_ANNOTATED,
    TOPIC_VISION_HEALTH,
    TOPIC_SET_CONFIDENCE
)

class SeezyVisionNode(Node):
    def __init__(self):
        super().__init__('seezy_vision_node')
        
        # 1. ROS 2 Publishers & Subscribers
        self.det_pub = self.create_publisher(String, TOPIC_VISION_DETECTIONS, 10)
        self.img_pub = self.create_publisher(Image, TOPIC_VISION_ANNOTATED, 10)
        self.health_pub = self.create_publisher(String, TOPIC_VISION_HEALTH, 10)
        
        # Dynamic Confidence State & Subscriber
        self.current_confidence = YOLO_CONFIDENCE_THRESHOLD
        self.conf_sub = self.create_subscription(Float32, TOPIC_SET_CONFIDENCE, self._conf_callback, 10)
        
        # 2. Load YOLOv8 TensorRT Engine
        current_dir = os.path.dirname(os.path.abspath(__file__))
        engine_path = os.path.join(current_dir, "models", MODEL_FILENAME)
        
        self.get_logger().info(f"Loading TensorRT Engine: {engine_path}")
        self.model = YOLO(engine_path, task='detect')
        
        # 3. Open Camera via V4L2
        self.get_logger().info(f"Opening camera {CAMERA_DEVICE} via V4L2...")
        self.cap = cv2.VideoCapture(CAMERA_DEVICE, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
        
        if not self.cap.isOpened():
            self.get_logger().error(f"Failed to open camera on {CAMERA_DEVICE}!")
            raise RuntimeError("Camera connection failed.")
            
        # 4. Start Dedicated Background Inference Thread
        self.get_logger().info(f"SeezyVisionNode active. Publishing to {TOPIC_VISION_DETECTIONS}")
        self.inference_thread = threading.Thread(target=self.camera_loop, daemon=True)
        self.inference_thread.start()

    def _conf_callback(self, msg: Float32):
        """Updates the internal YOLO confidence threshold dynamically."""
        self.current_confidence = msg.data
        self.get_logger().info(f"Confidence threshold updated to {self.current_confidence:.2f}")

    def camera_loop(self):
        """Continuous background inference loop."""
        while rclpy.ok():
            ret, frame = self.cap.read()
            if not ret:
                continue

            results = self.model(frame, verbose=False)
            
            # Publish Health Heartbeat (Model & Camera OK)
            health_msg = String()
            health_msg.data = "OK"
            self.health_pub.publish(health_msg)
            
            if len(results) > 0:
                boxes = results[0].boxes
                for box in boxes:
                    conf = float(box.conf[0])
                    # Use dynamic confidence threshold
                    if conf > self.current_confidence:
                        class_id = int(box.cls[0])
                        payload = {"class_id": class_id, "confidence": conf}
                        msg = String()
                        msg.data = json.dumps(payload)
                        self.det_pub.publish(msg)
                        self.get_logger().debug(f"Published Detection: Class {class_id} at {conf:.2f}")

            annotated_frame = results[0].plot()
            
            img_msg = Image()
            img_msg.header.stamp = self.get_clock().now().to_msg()
            img_msg.header.frame_id = "camera_link"
            img_msg.height = annotated_frame.shape[0]
            img_msg.width = annotated_frame.shape[1]
            img_msg.encoding = "bgr8"
            img_msg.is_bigendian = False
            img_msg.step = annotated_frame.shape[1] * 3
            img_msg.data = annotated_frame.tobytes()
            
            self.img_pub.publish(img_msg)

    def destroy_node(self):
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    try:
        node = SeezyVisionNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Vision Node Error: {e}")
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()