
import logging
import os
import sys
import subprocess
import re
import json
from typing import Any, Union, Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

# Global state for GPU availability
HAS_GPU = False
xp = None  # Will hold either numpy or cupy module

# Import numpy early as a fallback
import numpy as np


class GPUModel(Enum):
    """Supported GPU models."""
    RTX_3060TI = "RTX 3060 Ti"
    RTX_5070TI = "RTX 5070 Ti"
    UNKNOWN = "Unknown"


@dataclass
class GPUProperties:
    """Properties of a specific GPU model."""
    model: GPUModel
    cuda_cores: int
    vram_gb: int
    compute_capability: Tuple[int, int]
    memory_bandwidth_gbps: float
    recommended_batch_size: int
    max_batch_size: int
    memory_pool_size_mb: int


# GPU-specific configurations based on the provided information
GPU_CONFIGS: Dict[GPUModel, GPUProperties] = {
    GPUModel.RTX_3060TI: GPUProperties(
        model=GPUModel.RTX_3060TI,
        cuda_cores=12288,
        vram_gb=24,
        compute_capability=(8, 9),
        memory_bandwidth_gbps=608.0,
        recommended_batch_size=2048,
        max_batch_size=8192,
        memory_pool_size_mb=20480  # ~20GB pool, leaving ~4GB for system
    ),
    GPUModel.RTX_5070TI: GPUProperties(
        model=GPUModel.RTX_5070TI,
        cuda_cores=6144,
        vram_gb=16,
        compute_capability=(8, 9),
        memory_bandwidth_gbps=448.0,
        recommended_batch_size=1024,
        max_batch_size=4096,
        memory_pool_size_mb=13333  # ~13GB pool, leaving ~3GB for system
    ),
    GPUModel.UNKNOWN: GPUProperties(
        model=GPUModel.UNKNOWN,
        cuda_cores=0,
        vram_gb=0,
        compute_capability=(0, 0),
        memory_bandwidth_gbps=0.0,
        recommended_batch_size=512,
        max_batch_size=2048,
        memory_pool_size_mb=8192  # Conservative default
    )
}


@dataclass
class DetectedGPU:
    """Represents a detected GPU."""
    device_id: int
    model: GPUModel
    properties: GPUProperties
    total_memory_mb: int
    free_memory_mb: int
    is_available: bool = True


class GPUSelectionStrategy(Enum):
    """Strategies for GPU selection."""
    AUTO = "auto"  # Automatically select best available GPU
    SPECIFIC = "specific"  # Use a specific GPU by device ID
    FIRST = "first"  # Use the first available GPU
    MOST_VRAM = "most_vram"  # Use GPU with most VRAM
    MOST_CORES = "most_cores"  # Use GPU with most CUDA cores


# Global GPU state
_detected_gpus: List[DetectedGPU] = []
_selected_gpu: Optional[DetectedGPU] = None
_gpu_selection_strategy: GPUSelectionStrategy = GPUSelectionStrategy.AUTO
_specific_gpu_id: Optional[int] = None
_multi_gpu_enabled: bool = False
_active_gpus: List[int] = []  # List of device IDs for multi-GPU
_hw_gpu_info: List[Dict[str, Any]] = [] # Cached hardware-level detection


# Set CUDA environment variables before importing CuPy
# This is necessary for CuPy to find CUDA DLLs on Windows
def _setup_cuda_environment():
    """Set up CUDA environment variables for CuPy on Windows."""
    if sys.platform == 'win32':
        # Try to detect CUDA installation
        cuda_paths = [
            r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1',
            r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0',
            r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6',
            r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4',
            r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2',
            r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0',
        ]
        
        # Check if CUDA_PATH is already set
        if not os.environ.get('CUDA_PATH'):
            for cuda_path in cuda_paths:
                if os.path.exists(cuda_path):
                    os.environ['CUDA_PATH'] = cuda_path
                    logger.info(f"Set CUDA_PATH to: {cuda_path}")
                    break
        
        # Add CUDA bin to PATH if not already present
        cuda_path = os.environ.get('CUDA_PATH')
        if cuda_path:
            cuda_bin_paths = [
                os.path.join(cuda_path, 'bin', 'x64'),
                os.path.join(cuda_path, 'bin'),
            ]
            current_path = os.environ.get('PATH', '')
            for bin_path in cuda_bin_paths:
                if os.path.exists(bin_path) and bin_path not in current_path:
                    os.environ['PATH'] = bin_path + ';' + current_path
                    logger.info(f"Added CUDA bin to PATH: {bin_path}")
                    break


def _detect_gpu_model(device_id: int) -> GPUModel:
    """
    Detect the GPU model based on device properties.
    
    Args:
        device_id: CUDA device ID
        
    Returns:
        Detected GPUModel
    """
    global xp
    if not HAS_GPU or xp is None:
        return GPUModel.UNKNOWN
    
    try:
        import cupy as cp
        device = cp.cuda.Device(device_id)
        
        # safely decode name
        try:
            raw_name = getattr(device, 'name', "Unknown Device")
        except Exception:
            raw_name = "Unknown Device"

        if isinstance(raw_name, bytes):
             name = raw_name.decode('utf-8', errors='ignore').strip().upper()
        else:
             name = str(raw_name).strip().upper()
             
        logger.info(f"GPU Detection [Device {device_id}]: Name='{name}'")
        
        # Check for RTX 3060 Ti
        if '3060' in name and 'TI' in name:
            logger.info(f"Detected RTX 3060 Ti on device {device_id}")
            return GPUModel.RTX_3060TI
        
        # Check for RTX 5070 Ti
        if '5070' in name and 'TI' in name:
            logger.info(f"Detected RTX 5070 Ti on device {device_id}")
            return GPUModel.RTX_5070TI
            
        # Cross-reference with hardware detection if name is generic
        for hw in _hw_gpu_info:
            hw_name = hw['name'].upper()
            if '3060' in hw_name and 'TI' in hw_name:
                logger.info(f"Matched RTX 3060 Ti from hardware hint for device {device_id}")
                return GPUModel.RTX_3060TI
            if '5070' in hw_name and 'TI' in hw_name:
                logger.info(f"Matched RTX 5070 Ti from hardware hint for device {device_id}")
                return GPUModel.RTX_5070TI
        
        # Try to infer from memory and compute capability
        total_memory_mb = device.mem_info[0] // (1024 * 1024)
        compute_capability = device.compute_capability
        logger.info(f"Analysis [Device {device_id}]: Memory={total_memory_mb}MB, CC={compute_capability}")
        
        # Heuristic detection based on memory size
        if total_memory_mb >= 23000:  # ~24GB
            logger.info(f"Inferred RTX 3060 Ti on device {device_id} based on memory ({total_memory_mb}MB)")
            return GPUModel.RTX_3060TI
        elif total_memory_mb >= 15000:  # ~16GB
            logger.info(f"Inferred RTX 5070 Ti on device {device_id} based on memory ({total_memory_mb}MB)")
            return GPUModel.RTX_5070TI
        
        logger.warning(f"Unknown GPU model on device {device_id}: {device.name}")
        return GPUModel.UNKNOWN
        
    except Exception as e:
        logger.error(f"Error detecting GPU model for device {device_id}: {e}")
        return GPUModel.UNKNOWN


def _detect_via_nvidia_smi() -> List[Dict[str, Any]]:
    """Uses nvidia-smi to detect NVIDIA GPUs."""
    try:
        cmd = ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        gpus = []
        for line in result.stdout.strip().split('\n'):
            if ',' in line:
                name, mem = line.split(',')
                gpus.append({
                    "name": name.strip(),
                    "memory_mb": int(mem.strip())
                })
        return gpus
    except (subprocess.SubprocessError, FileNotFoundError, ValueError):
        return []


def _detect_via_wmi_powershell() -> List[Dict[str, Any]]:
    """Uses PowerShell to detect all GPUs (Cross-vendor)."""
    try:
        # Use PowerShell to get video controller info
        # Get-CimInstance is more modern than wmic
        ps_cmd = 'Get-CimInstance -ClassName Win32_VideoController | Select-Object Name, AdapterRAM | ConvertTo-Json'
        cmd = ["powershell", "-Command", ps_cmd]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if not result.stdout.strip():
            return []
            
        data = json.loads(result.stdout)
        if isinstance(data, dict):
            data = [data]
            
        gpus = []
        for entry in data:
            name = entry.get("Name", "Unknown")
            # AdapterRAM can be negative or weird in WMI for large values, but we'll try
            ram_raw = entry.get("AdapterRAM", 0)
            ram_mb = abs(int(ram_raw)) // (1024 * 1024) if ram_raw else 0
            
            gpus.append({
                "name": name,
                "memory_mb": ram_mb
            })
        return gpus
    except (subprocess.SubprocessError, FileNotFoundError, Exception):
        return []


def get_hardware_gpu_info() -> List[Dict[str, Any]]:
    """
    Detects hardware GPUs installed in the PC using OS-level commands.
    Returns a list of GPU info dicts.
    """
    # 1. Try nvidia-smi first for detailed NVIDIA info
    gpus = _detect_via_nvidia_smi()
    if gpus:
        return gpus
        
    # 2. Fallback to WMI/PowerShell for generic detection (includes AMD/Intel)
    if sys.platform == 'win32':
        return _detect_via_wmi_powershell()
        
    return []


def _detect_all_gpus() -> List[DetectedGPU]:
    """
    Detect all available GPUs and their properties.
    
    Returns:
        List of DetectedGPU objects
    """
    global xp, HAS_GPU
    detected = []
    
    if not HAS_GPU or xp is None:
        return detected
    
    try:
        import cupy as cp
        device_count = cp.cuda.runtime.getDeviceCount()
        
        for device_id in range(device_count):
            try:
                device = cp.cuda.Device(device_id)
                model = _detect_gpu_model(device_id)
                properties = GPU_CONFIGS[model]
                
                total_memory, free_memory = device.mem_info
                total_memory_mb = total_memory // (1024 * 1024)
                free_memory_mb = free_memory // (1024 * 1024)
                
                detected_gpu = DetectedGPU(
                    device_id=device_id,
                    model=model,
                    properties=properties,
                    total_memory_mb=total_memory_mb,
                    free_memory_mb=free_memory_mb,
                    is_available=True
                )
                detected.append(detected_gpu)
                
                logger.info(
                    f"GPU {device_id}: {model.value} - "
                    f"{total_memory_mb}MB total, {free_memory_mb}MB free, "
                    f"{properties.cuda_cores} CUDA cores"
                )
                
            except Exception as e:
                logger.error(f"Error detecting GPU {device_id}: {e}")
                
    except Exception as e:
        logger.error(f"Error detecting GPUs: {e}")
    
    return detected


def _select_gpu(strategy: GPUSelectionStrategy = GPUSelectionStrategy.AUTO, 
                 specific_id: Optional[int] = None) -> Optional[DetectedGPU]:
    """
    Select a GPU based on the specified strategy.
    
    Args:
        strategy: Selection strategy to use
        specific_id: Specific GPU device ID (for SPECIFIC strategy)
        
    Returns:
        Selected DetectedGPU or None
    """
    global _detected_gpus
    
    if not _detected_gpus:
        return None
    
    available_gpus = [gpu for gpu in _detected_gpus if gpu.is_available]
    if not available_gpus:
        return None
    
    if strategy == GPUSelectionStrategy.SPECIFIC and specific_id is not None:
        for gpu in available_gpus:
            if gpu.device_id == specific_id:
                logger.info(f"Selected specific GPU: {gpu.model.value} (device {gpu.device_id})")
                return gpu
        logger.warning(f"GPU {specific_id} not found, falling back to auto selection")
        strategy = GPUSelectionStrategy.AUTO
    
    if strategy == GPUSelectionStrategy.FIRST:
        selected = available_gpus[0]
        logger.info(f"Selected first available GPU: {selected.model.value} (device {selected.device_id})")
        return selected
    
    if strategy == GPUSelectionStrategy.MOST_VRAM:
        selected = max(available_gpus, key=lambda g: g.total_memory_mb)
        logger.info(f"Selected GPU with most VRAM: {selected.model.value} (device {selected.device_id})")
        return selected
    
    if strategy == GPUSelectionStrategy.MOST_CORES:
        selected = max(available_gpus, key=lambda g: g.properties.cuda_cores)
        logger.info(f"Selected GPU with most CUDA cores: {selected.model.value} (device {selected.device_id})")
        return selected
    
    # AUTO strategy: prioritize known GPUs, then by VRAM
    known_gpus = [gpu for gpu in available_gpus if gpu.model != GPUModel.UNKNOWN]
    if known_gpus:
        # Prefer RTX 3060Ti for its higher core count and VRAM
        rtx_3060ti = [gpu for gpu in known_gpus if gpu.model == GPUModel.RTX_3060TI]
        if rtx_3060ti:
            selected = rtx_3060ti[0]
            logger.info(f"Auto-selected RTX 3060 Ti (device {selected.device_id})")
            return selected
        
        # Fall back to RTX 5070Ti
        rtx_5070ti = [gpu for gpu in known_gpus if gpu.model == GPUModel.RTX_5070TI]
        if rtx_5070ti:
            selected = rtx_5070ti[0]
            logger.info(f"Auto-selected RTX 5070 Ti (device {selected.device_id})")
            return selected
    
    # Fall back to GPU with most VRAM
    selected = max(available_gpus, key=lambda g: g.total_memory_mb)
    logger.info(f"Auto-selected GPU with most VRAM: {selected.model.value} (device {selected.device_id})")
    return selected


def check_gpu_availability():
    """
    Checks if CuPy is installed AND functioning correctly.
    Performs a smoke test to ensure CUDA libs (NVRTC) are loadable.
    Sets global HAS_GPU and xp variables.
    Also detects all available GPUs and selects the best one.
    """
    global HAS_GPU, xp, _detected_gpus, _selected_gpu, _hw_gpu_info
    
    # Phase 0: Hardware Auto-Detection (Regardless of CuPy)
    try:
        _hw_gpu_info = get_hardware_gpu_info()
        if _hw_gpu_info:
            for i, gpu in enumerate(_hw_gpu_info):
                logger.info(f"Hardware GPU detected [{i}]: {gpu['name']} ({gpu['memory_mb']}MB VRAM)")
        else:
            logger.info("No hardware GPU detected via OS-level commands (fallback to CPU defaults).")
    except Exception as e:
        logger.debug(f"Hardware detection failed: {e}")

    try:
        import cupy as cp
        # Smoke Test: Attempt a small allocation and kernel compile check
        # Many environments have cupy installed but missing CUDA DLLs (nvrtc)
        with cp.cuda.Device(0):
            a = cp.array([1, 2, 3])
            b = cp.array([4, 5, 6])
            c = a + b # Triggers basic kernel compilation/execution
            c.get()   # Sync
            
        HAS_GPU = True
        xp = cp
        device_count = cp.cuda.runtime.getDeviceCount()
        logger.info(f"GPU Acceleration Enabled: CuPy detected with {device_count} device(s) and passed smoke test.")
        
        # Detect all GPUs
        _detected_gpus = _detect_all_gpus()
        
        # Select GPU based on current strategy
        _selected_gpu = _select_gpu(_gpu_selection_strategy, _specific_gpu_id)
        
        if _selected_gpu:
            # Set the selected GPU as current
            cp.cuda.Device(_selected_gpu.device_id).use()
            logger.info(f"Using GPU {_selected_gpu.device_id}: {_selected_gpu.model.value}")
            
            # Configure memory pool based on GPU properties
            mempool = cp.get_default_memory_pool()
            mempool.set_limit(size=_selected_gpu.properties.memory_pool_size_mb * 1024 * 1024)
            logger.info(f"Memory pool set to {_selected_gpu.properties.memory_pool_size_mb}MB")
            
    except (ImportError, Exception) as e:
        HAS_GPU = False
        xp = np
        _detected_gpus = []
        _selected_gpu = None
        if isinstance(e, ImportError):
            logger.warning("GPU Acceleration Disabled: CuPy not found. Falling back to NumPy.")
        else:
            logger.error(f"GPU Acceleration Failed: CuPy installed but failed smoke test ({e}). Falling back to NumPy.")


def set_gpu_selection_strategy(strategy: Union[GPUSelectionStrategy, str], 
                                specific_gpu_id: Optional[int] = None):
    """
    Set the GPU selection strategy.
    
    Args:
        strategy: Selection strategy (GPUSelectionStrategy enum or string)
        specific_gpu_id: Specific GPU device ID (for SPECIFIC strategy)
    """
    global _gpu_selection_strategy, _specific_gpu_id, _selected_gpu
    
    if isinstance(strategy, str):
        try:
            strategy = GPUSelectionStrategy(strategy.lower())
        except ValueError:
            logger.error(f"Invalid GPU selection strategy: {strategy}")
            return
    
    _gpu_selection_strategy = strategy
    _specific_gpu_id = specific_gpu_id
    
    # Re-select GPU if available
    if HAS_GPU and _detected_gpus:
        _selected_gpu = _select_gpu(strategy, specific_gpu_id)
        if _selected_gpu:
            import cupy as cp
            cp.cuda.Device(_selected_gpu.device_id).use()
            logger.info(f"GPU selection changed to: {_selected_gpu.model.value} (device {_selected_gpu.device_id})")


def enable_multi_gpu(gpu_ids: Optional[List[int]] = None):
    """
    Enable multi-GPU mode.
    
    Args:
        gpu_ids: List of GPU device IDs to use. If None, uses all available GPUs.
    """
    global _multi_gpu_enabled, _active_gpus
    
    if not HAS_GPU:
        logger.warning("Cannot enable multi-GPU: No GPU available")
        return
    
    if gpu_ids is None:
        _active_gpus = [gpu.device_id for gpu in _detected_gpus if gpu.is_available]
    else:
        valid_ids = [gpu_id for gpu_id in gpu_ids if gpu_id < len(_detected_gpus)]
        _active_gpus = valid_ids
    
    if len(_active_gpus) > 1:
        _multi_gpu_enabled = True
        logger.info(f"Multi-GPU enabled with devices: {_active_gpus}")
    else:
        _multi_gpu_enabled = False
        logger.info(f"Multi-GPU disabled (only {len(_active_gpus)} device(s) available)")


def disable_multi_gpu():
    """Disable multi-GPU mode and return to single GPU."""
    global _multi_gpu_enabled, _active_gpus, _selected_gpu
    
    _multi_gpu_enabled = False
    _active_gpus = []
    
    if _selected_gpu:
        import cupy as cp
        cp.cuda.Device(_selected_gpu.device_id).use()
        logger.info(f"Multi-GPU disabled, using GPU {_selected_gpu.device_id}")


def get_detected_gpus() -> List[DetectedGPU]:
    """Get list of all detected GPUs."""
    return _detected_gpus


def get_selected_gpu() -> Optional[DetectedGPU]:
    """Get the currently selected GPU."""
    return _selected_gpu


def is_multi_gpu_enabled() -> bool:
    """Check if multi-GPU mode is enabled."""
    return _multi_gpu_enabled


def get_active_gpu_ids() -> List[int]:
    """Get list of active GPU device IDs."""
    return _active_gpus


def get_gpu_config() -> Optional[GPUProperties]:
    """Get the configuration for the currently selected GPU."""
    if _selected_gpu:
        return _selected_gpu.properties
    return None


def get_recommended_batch_size() -> int:
    """Get the recommended batch size for the current GPU."""
    config = get_gpu_config()
    if config:
        return config.recommended_batch_size
    return 512  # Default fallback


def get_max_batch_size() -> int:
    """Get the maximum batch size for the current GPU."""
    config = get_gpu_config()
    if config:
        return config.max_batch_size
    return 2048  # Default fallback


# Call setup before any CuPy import
_setup_cuda_environment()

# Perform the check on module load
check_gpu_availability()


def apply_gpu_config(gpu_config: Dict[str, Any]):
    """
    Applies GPU settings from the game configuration.
    
    Args:
        gpu_config: The 'gpu' section of the configuration dictionary.
    """
    global _gpu_selection_strategy, _specific_gpu_id, _multi_gpu_enabled, _active_gpus
    
    if not gpu_config:
        return
        
    enabled = gpu_config.get("enabled", True)
    if not enabled:
        global HAS_GPU, xp
        HAS_GPU = False
        xp = np
        return
        
    # Selection Strategy
    strategy_str = gpu_config.get("selection_strategy", "auto")
    specific_id = gpu_config.get("specific_gpu_id")
    
    set_gpu_selection_strategy(strategy_str, specific_id)
    
    # Custom Profiles
    custom_profiles = gpu_config.get("gpu_profiles", {})
    for model_name, props in custom_profiles.items():
        try:
            # Update or Add to GPU_CONFIGS
            model_enum = None
            for m in GPUModel:
                if m.name == model_name or m.value == model_name:
                    model_enum = m
                    break
            
            if not model_enum:
                # Dynamic model registration could be complex, for now we only support known enums
                # but we can update the selected GPU properties directly if it matches the specific_id
                pass
            
            if model_enum:
                GPU_CONFIGS[model_enum] = GPUProperties(
                    model=model_enum,
                    cuda_cores=props.get("cuda_cores", 0),
                    vram_gb=props.get("vram_gb", 0),
                    compute_capability=tuple(props.get("compute_capability", [0, 0])),
                    memory_bandwidth_gbps=props.get("memory_bandwidth_gbps", 0.0),
                    recommended_batch_size=props.get("recommended_batch_size", 512),
                    max_batch_size=props.get("max_batch_size", 2048),
                    memory_pool_size_mb=props.get("memory_pool_size_mb", 8192)
                )
        except Exception as e:
            logger.error(f"Error applying custom GPU profile for {model_name}: {e}")

    # Multi-GPU
    if gpu_config.get("multi_gpu_enabled", False):
        enable_multi_gpu(gpu_config.get("multi_gpu_device_ids"))
    
    # Batch Size / Memory Overrides (Manual)
    # These would typically override the profile-based defaults if set
    
    # Refresh selected GPU to pick up profile changes
    if _selected_gpu:
        import cupy as cp
        mempool = cp.get_default_memory_pool()
        pool_size = gpu_config.get("memory_pool_size_mb") or _selected_gpu.properties.memory_pool_size_mb
        mempool.set_limit(size=pool_size * 1024 * 1024)
        logger.info(f"GPU Settings Updated from Config. Memory pool: {pool_size}MB")

def get_xp():
    """Returns the active array module (cupy or numpy)."""
    return xp


def is_available() -> bool:
    """Returns True if GPU acceleration is available and enabled."""
    return HAS_GPU

def is_vectorization_enabled() -> bool:
    """Returns True if either CuPy or NumPy is available for vectorized operations."""
    return xp is not None


def to_gpu(array_like: Any, device_id: Optional[int] = None) -> Any:
    """
    Moves data to the GPU if available.
    If input is already a cupy array or GPU is unavailable, returns as is (or converts to numpy).
    
    Args:
        array_like: Data to move to GPU
        device_id: Specific GPU device ID (for multi-GPU). If None, uses selected GPU.
    """
    if not HAS_GPU:
        return xp.array(array_like) if not isinstance(array_like, xp.ndarray) else array_like
    
    # If it's already a cupy array, return it
    if isinstance(array_like, xp.ndarray):
        return array_like
        
    # Handle multi-GPU device selection
    if device_id is not None and device_id != xp.cuda.Device().id:
        with xp.cuda.Device(device_id):
            return xp.array(array_like)
    
    return xp.array(array_like)


def to_cpu(array_like: Any) -> Any:
    """
    Moves data to the CPU (NumPy array).
    """
    if not HAS_GPU:
        # It's already numpy (or list/scalar)
        return xp.array(array_like) if not isinstance(array_like, xp.ndarray) else array_like
        
    if hasattr(array_like, 'get'): # CuPy array
        return array_like.get()
    
    # It might be a numpy array already or a list
    import numpy as np
    return np.array(array_like) if not isinstance(array_like, np.ndarray) else array_like


def ensure_list(array_like: Any) -> list:
    """Converts a GPU or CPU array back to a standard Python list."""
    arr = to_cpu(array_like)
    if hasattr(arr, 'tolist'):
        return arr.tolist()
    return list(arr)


def synchronize():
    """
    Blocks until all GPU operations in the current stream are complete.
    No-op if running on CPU.
    """
    if HAS_GPU:
        xp.cuda.Stream.null.synchronize()


def clean_memory():
    """
    Explicitly frees GPU memory pool (garbage collection equivalent).
    """
    if HAS_GPU:
        mempool = xp.get_default_memory_pool()
        pinned_mempool = xp.get_default_pinned_memory_pool()
        mempool.free_all_blocks()
        pinned_mempool.free_all_blocks()


def get_memory_info() -> Optional[Dict[str, int]]:
    """
    Get memory information for the current GPU.
    
    Returns:
        Dictionary with 'total_mb', 'free_mb', 'used_mb' or None if no GPU
    """
    if not HAS_GPU or _selected_gpu is None:
        return None
    
    try:
        import cupy as cp
        device = cp.cuda.Device(_selected_gpu.device_id)
        total, free = device.mem_info
        return {
            'total_mb': total // (1024 * 1024),
            'free_mb': free // (1024 * 1024),
            'used_mb': (total - free) // (1024 * 1024)
        }
    except Exception as e:
        logger.error(f"Error getting memory info: {e}")
        return None



# Dedup set for backend logging
_logged_components = set()

def log_backend_usage(component_name: str, logger_instance: logging.Logger):
    """
    Helper to log the current backend status for a specific component.
    Logs only ONCE per component to avoid spam.
    """
    if component_name in _logged_components:
        return
        
    _logged_components.add(component_name)
    
    backend = "GPU (CuPy)" if HAS_GPU else "CPU (NumPy)"
    device_info = ""
    if HAS_GPU and _selected_gpu:
        try:
             # Ensure model name is cleaner
             model_name = _selected_gpu.model.value
             device_info = f" [Device: {_selected_gpu.device_id} ({model_name})]"
        except:
             device_info = f" [Device: {_selected_gpu.device_id}]"
    
    logger_instance.info(f"[{component_name}] Logic backend initialized using: {backend}{device_info}")

class GPUTracker:
    """
    Tracks GPU usage and provides optimized memory management based on GPU type.
    """
    
    def __init__(self, component_name: str):
        """
        Initialize GPU tracker for a specific component.
        
        Args:
            component_name: Name of the component using GPU
        """
        self.component_name = component_name
        self.gpu_config = get_gpu_config()
        self.device_id = _selected_gpu.device_id if _selected_gpu else None
        self.memory_pool_size = self.gpu_config.memory_pool_size_mb * 1024 * 1024 if self.gpu_config else 0
        self.recommended_batch_size = self.gpu_config.recommended_batch_size if self.gpu_config else 512
        self.max_batch_size = self.gpu_config.max_batch_size if self.gpu_config else 2048
        self.cuda_cores = self.gpu_config.cuda_cores if self.gpu_config else 0
        self.vram_gb = self.gpu_config.vram_gb if self.gpu_config else 0
        
        # Only log init once per component name to avoid spam
        if component_name not in _logged_components:
             logger.info(
                f"[{component_name}] GPUTracker initialized: "
                f"GPU={self.gpu_config.model.value if self.gpu_config else 'None'}, "
                f"CUDA Cores={self.cuda_cores}, VRAM={self.vram_gb}GB, "
                f"Recommended Batch Size={self.recommended_batch_size}"
             )
    
    def get_optimal_batch_size(self, base_size: Optional[int] = None) -> int:
        """
        Get the optimal batch size for the current GPU.
        
        Args:
            base_size: Base batch size requested. If None, uses GPU's recommended size.
            
        Returns:
            Optimal batch size for the current GPU
        """
        if base_size is None:
            return self.recommended_batch_size
        
        # Scale based on GPU capabilities
        if self.cuda_cores >= 10000:  # RTX 3060Ti
            return min(base_size * 2, self.max_batch_size)
        elif self.cuda_cores >= 6000:  # RTX 5070Ti
            return min(base_size, self.max_batch_size)
        else:
            return min(base_size // 2, self.max_batch_size)
    
    def get_memory_pool_size(self) -> int:
        """Get the memory pool size in bytes."""
        return self.memory_pool_size
    
    def get_memory_info(self) -> Optional[Dict[str, int]]:
        """Get current memory usage information."""
        return get_memory_info()
    
    def check_memory_available(self, required_mb: int) -> bool:
        """
        Check if enough memory is available.
        
        Args:
            required_mb: Required memory in MB
            
        Returns:
            True if enough memory is available
        """
        mem_info = self.get_memory_info()
        if mem_info is None:
            return False
        return mem_info['free_mb'] >= required_mb
    
    def log_status(self, logger_instance: Optional[logging.Logger] = None):
        """Log current GPU status."""
        log_target = logger_instance or logger
        mem_info = self.get_memory_info()
        
        status = (
            f"[{self.component_name}] GPU Status: "
            f"Model={self.gpu_config.model.value if self.gpu_config else 'None'}, "
            f"Device={self.device_id}, "
            f"CUDA Cores={self.cuda_cores}, "
            f"VRAM={self.vram_gb}GB"
        )
        
        if mem_info:
            status += f", Memory: {mem_info['used_mb']}MB/{mem_info['total_mb']}MB used ({mem_info['free_mb']}MB free)"
        
        log_target.info(status)

def cleanup_gpu_resources():
    """
    Optimization 2.4: Explicit GPU resource cleanup and memory pool optimization.
    Call this at the end of a turn cycle to free unused VRAM.
    """
    global HAS_GPU, xp
    if not HAS_GPU or xp is None:
        return
        
    try:
        import cupy as cp
        # Clear the memory pool
        mempool = cp.get_default_memory_pool()
        pinned_mempool = cp.get_default_pinned_memory_pool()
        
        mempool.free_all_blocks()
        pinned_mempool.free_all_blocks()
        
        logger.info("[GPU] Explicit cleanup complete: Memory pools flushed.")
    except Exception as e:
        logger.error(f"[GPU] Error during cleanup: {e}")

def set_memory_limit(limit_mb: int):
    """Sets a limit on the amount of GPU memory CuPy can use."""
    global HAS_GPU, xp
    if not HAS_GPU or xp is None:
        return
        
    try:
        import cupy as cp
        cp.get_default_memory_pool().set_limit(size=limit_mb * 1024 * 1024)
        logger.info(f"[GPU] Memory limit set to {limit_mb} MB")
    except Exception as e:
        logger.error(f"[GPU] Error setting memory limit: {e}")
