import os
import time
import cv2
import pandas as pd
from ultralytics import YOLO
from jtop import jtop

# ==========================================
# BENCHMARK CONFIGURATION
# ==========================================
WORKSPACE = os.path.expanduser("~/SEEZY/Image Processing")
MODELS_DIR = os.path.join(WORKSPACE, "models")
RESULTS_DIR = os.path.join(WORKSPACE, "results")
CSV_PATH = os.path.join(RESULTS_DIR, "jetson_benchmark_results.csv")

# Strictly Controlled Parameters
CAMERA_INDEX = "/dev/video0"
CAPTURE_RES = (1280, 720)
IMGSZ = 640
CONF_THRESH = 0.25
WARMUP_FRAMES = 50
BENCHMARK_FRAMES = 300

MODELS_TO_TEST = [
    "expA_yolov8n.engine",
    "expA_yolov8s.engine",
    "expA_yolov8m.engine"
]

def run_benchmark(model_file, jetson):
    model_path = os.path.join(MODELS_DIR, model_file)
    if not os.path.exists(model_path):
        print(f"⚠️ Missing engine file: {model_path}")
        return None

    print(f"\n🚀 Loading {model_file}...")
    model = YOLO(model_path, task='detect')
    
    # Initialize Logitech Brio 500 with strict V4L2 backend to prevent Bad File Descriptor errors
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_RES[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_RES[1])
    
    if not cap.isOpened():
        print("❌ Failed to open camera. Check /dev/video0.")
        return None

    print(f"🔥 Warming up GPU for {WARMUP_FRAMES} frames...")
    for _ in range(WARMUP_FRAMES):
        ret, frame = cap.read()
        if ret:
            model.predict(frame, imgsz=IMGSZ, conf=CONF_THRESH, verbose=False)

    print(f"📊 Starting benchmark: {BENCHMARK_FRAMES} frames...")
    
    total_pipeline_time = 0.0
    total_inference_time = 0.0
    total_objects = 0
    gpu_util_list = []
    vram_list = []
    power_list = []
    valid_frames_processed = 0

    for _ in range(BENCHMARK_FRAMES):
        # 1. Pipeline Start (Capture)
        t_pipeline_start = time.perf_counter()
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Camera frame dropped mid-benchmark!")
            break
            
        valid_frames_processed += 1

        # 2. Inference Start
        t_infer_start = time.perf_counter()
        results = model.predict(frame, imgsz=IMGSZ, conf=CONF_THRESH, verbose=False)
        t_infer_end = time.perf_counter()

        # 3. Pipeline End
        t_pipeline_end = time.perf_counter()

        # Record Timings (ms)
        inference_latency = (t_infer_end - t_infer_start) * 1000
        pipeline_latency = (t_pipeline_end - t_pipeline_start) * 1000
        
        total_inference_time += inference_latency
        total_pipeline_time += pipeline_latency
        total_objects += len(results[0].boxes)

        # 4. Safe Hardware Metrics Extraction via jtop
        if jetson.ok():
            gpu_data = jetson.gpu.get('gpu', {})
            gpu_status = gpu_data.get('status', 0)
            
            # Safely extract integer load whether it's a dict or flat number
            if isinstance(gpu_status, dict):
                gpu_util = gpu_status.get('load', 0)
            else:
                gpu_util = gpu_status
                
            gpu_util_list.append(gpu_util)
            vram_list.append(jetson.memory['RAM']['used'] / 1024) # Convert to MB
            power_list.append(jetson.power['tot']['power'])       # mW

    cap.release()
    
    if valid_frames_processed == 0:
        print("❌ Benchmark failed: 0 valid frames captured.")
        return None

    # Averages Calculation based on actual frames processed
    avg_infer_latency = total_inference_time / valid_frames_processed
    avg_pipeline_latency = total_pipeline_time / valid_frames_processed
    avg_infer_fps = 1000.0 / avg_infer_latency if avg_infer_latency > 0 else 0
    avg_pipeline_fps = 1000.0 / avg_pipeline_latency if avg_pipeline_latency > 0 else 0
    
    avg_gpu_util = sum(gpu_util_list) / len(gpu_util_list) if gpu_util_list else 0
    avg_vram = sum(vram_list) / len(vram_list) if vram_list else 0
    avg_power = sum(power_list) / len(power_list) if power_list else 0
    avg_detections = total_objects / valid_frames_processed

    return {
        "Model": model_file.split('.')[0],
        "Infer Latency (ms)": round(avg_infer_latency, 2),
        "Infer FPS": round(avg_infer_fps, 1),
        "Pipeline FPS": round(avg_pipeline_fps, 1),
        "GPU Util (%)": round(avg_gpu_util, 1),
        "VRAM Used (MB)": round(avg_vram, 0),
        "Power (mW)": round(avg_power, 0),
        "Avg Detections": round(avg_detections, 2)
    }

def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    results_data = []

    # Launch jtop daemon context once
    with jtop() as jetson:
        for model_file in MODELS_TO_TEST:
            metrics = run_benchmark(model_file, jetson)
            if metrics:
                results_data.append(metrics)
                print(f"✅ Completed: {metrics['Model']} -> Model FPS: {metrics['Infer FPS']}")

    if results_data:
        df = pd.DataFrame(results_data)
        print("\n=======================================================")
        print("          JETSON ORIN NANO HARDWARE BENCHMARK          ")
        print("=======================================================")
        print(df.to_string(index=False))
        
        df.to_csv(CSV_PATH, index=False)
        print(f"\n📁 Benchmark saved to: {CSV_PATH}")

if __name__ == "__main__":
    main()