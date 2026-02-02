
import sys
import os
import logging

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

from src.core import gpu_utils

def verify_gpu_detection():
    print("Verifying GPU Detection...")
    
    # 1. Hardware Detection
    print("\n[Step 1] Hardware Detection (OS Level)")
    hw_info = gpu_utils.get_hardware_gpu_info()
    if hw_info:
        for gpu in hw_info:
            print(f"  - Detected: {gpu}")
    else:
        print("  - No hardware GPU detected via OS commands (VM or non-NVIDIA/Windows?).")
        
    # 2. CuPy Detection
    print("\n[Step 2] CuPy/Runtime Detection")
    gpu_utils.check_gpu_availability()
    if gpu_utils.is_available():
        print(f"  - GPU Acceleration: ENABLED")
        print(f"  - Backend: {gpu_utils.get_xp().__name__}")
        
        selected = gpu_utils.get_selected_gpu()
        if selected:
            print(f"  - Selected GPU: {selected.model.value} (Device {selected.device_id})")
            print(f"  - VRAM: {selected.properties.vram_gb} GB")
        else:
            print("  - No GPU selected despite availability?")
    else:
        print("  - GPU Acceleration: DISABLED (NumPy Fallback)")
        
    print("\nGPU Verification Complete.")

if __name__ == "__main__":
    verify_gpu_detection()
