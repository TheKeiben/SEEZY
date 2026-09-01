import os
import shutil
import subprocess

WORKSPACE = os.path.expanduser("~/SEEZY/Image Processing")
MODELS_DIR = os.path.join(WORKSPACE, "models")

MODELS_TO_CONVERT = [
    "expA_yolov8n.onnx",
    "expA_yolov8s.onnx",
    "expA_yolov8m.onnx"
]

def find_trtexec():
    """Locates the trtexec executable on the system."""
    # First, check if it's already in the global system path
    trtexec_bin = shutil.which("trtexec")
    if trtexec_bin:
        return trtexec_bin
    
    # Otherwise, manually check standard JetPack installation locations
    common_paths = [
        "/usr/bin/trtexec",
        "/usr/local/tensorrt/bin/trtexec",
        "/usr/src/tensorrt/bin/trtexec",
        "/usr/local/cuda/bin/trtexec"
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    return None

def main():
    print("=======================================================")
    print("        TENSORRT TRTEXEC ENGINE CONVERTER (SEEZY)      ")
    print("=======================================================")

    trtexec_path = find_trtexec()
    if not trtexec_path:
        print("❌ Could not find trtexec. Ensure 'tensorrt-dev' is fully installed.")
        return

    print(f"🔍 Found trtexec compiler at: {trtexec_path}\n")

    for onnx_file in MODELS_TO_CONVERT:
        onnx_path = os.path.join(MODELS_DIR, onnx_file)
        engine_file = onnx_file.replace(".onnx", ".engine")
        engine_path = os.path.join(MODELS_DIR, engine_file)

        if not os.path.exists(onnx_path):
            print(f"⚠️ ONNX file not found, skipping: {onnx_path}")
            continue

        if os.path.exists(engine_path):
            print(f"ℹ️ Engine already exists, skipping: {engine_file}")
            continue

        # Build the exact trtexec terminal command with FP16 precision
        cmd = [
            trtexec_path,
            f"--onnx={onnx_path}",
            f"--saveEngine={engine_path}",
            "--fp16"
        ]

        print(f"🚀 Compiling: {onnx_file} -> {engine_file}")
        print(f"   (This usually takes 10-15 minutes per model...)")
        
        # Run the command and suppress the massive wall of text unless it fails
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        
        if result.returncode == 0:
            print(f"   ✅ Successfully built: {engine_file}\n")
        else:
            print(f"   ❌ Failed to build: {engine_file}. Run the command manually to see errors.\n")

if __name__ == "__main__":
    main()