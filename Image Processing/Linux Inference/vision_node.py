#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Image
import cv2
import json
import threading
from ultralytics import YOLO

class SeezyVisionNode(Node):
    def __init__(self):
        super().__init__('seezy_vision_node')
        
        # 1. ROS 2 Publishers (cv_bridge bypassed to prevent KeyError 16)
        self.det_pub = self.create_publisher(String, '/seezy/detections', 10)
        self.img_pub = self.create_publisher(Image, '/seezy/camera/annotated', 10)
        
        # 2. Load YOLOv8 TensorRT Engine
        engine_path = "/home/seezy-pc/SEEZY/Image Processing/models/expA_yolov8n.engine" 
        self.get_logger().info(f"Loading TensorRT Engine: {engine_path}")
        self.model = YOLO(engine_path, task='detect')
        
        # 3. Open Camera
        self.get_logger().info("Opening Brio 500 via strict V4L2 on SuperSpeed USB...")
        self.cap = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        if not self.cap.isOpened():
            self.get_logger().error("Failed to open Logitech Brio 500!")
            raise RuntimeError("Camera connection failed.")
            
        # 4. Start Dedicated Background Thread
        self.get_logger().info("SeezyVisionNode active. Publishing to /seezy/detections")
        self.inference_thread = threading.Thread(target=self.camera_loop, daemon=True)
        self.inference_thread.start()

    def camera_loop(self):
        """Continuous background inference loop."""
        while rclpy.ok():
            ret, frame = self.cap.read()
            if not ret:
                continue

            # Pass the raw 1280x720 HD frame directly to the model
            results = self.model(frame, verbose=False)
            
            if len(results) > 0:
                boxes = results[0].boxes
                for box in boxes:
                    conf = float(box.conf[0])
                    if conf > 0.6:
                        class_id = int(box.cls[0])
                        payload = {"class_id": class_id, "confidence": conf}
                        msg = String()
                        msg.data = json.dumps(payload)
                        self.det_pub.publish(msg)
                        self.get_logger().debug(f"Published Detection: Class {class_id} at {conf:.2f}")

            # Plot bounding boxes onto the raw 1280x720 frame
            annotated_frame = results[0].plot()
            
            # Manually pack the ROS 2 Image message (Bypasses cv_bridge Numpy 2.0 bug)
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