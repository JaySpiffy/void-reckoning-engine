"""
Test multi-GPU support for the multi-universe simulator.

Tests GPU detection, configuration, and selection logic for RTX 3060Ti and RTX 5070Ti.
"""

import pytest
import sys
from unittest.mock import Mock, MagicMock, patch, PropertyMock

pytestmark = pytest.mark.skip(reason="CuPy compatibility issue")

# Add src to path for imports
sys.path.insert(0, 'src')

from src.core.gpu_utils import (
    GPUModel,
    GPUProperties,
    DetectedGPU,
    GPUSelectionStrategy,
    GPU_CONFIGS,
    _detect_gpu_model,
    _select_gpu,
    _detect_all_gpus,
    set_gpu_selection_strategy,
    enable_multi_gpu,
    disable_multi_gpu,
    get_detected_gpus,
    get_selected_gpu,
    is_multi_gpu_enabled,
    get_active_gpu_ids,
    get_gpu_config,
    get_recommended_batch_size,
    get_max_batch_size,
    get_memory_info,
    GPUTracker,
    HAS_GPU,
    xp
)


class TestGPUModel:
    """Test GPUModel enum."""
    
    def test_gpu_model_values(self):
        """Test GPUModel enum values."""
        assert GPUModel.RTX_3060TI.value == "RTX 3060 Ti"
        assert GPUModel.RTX_5070TI.value == "RTX 5070 Ti"
        assert GPUModel.UNKNOWN.value == "Unknown"


class TestGPUProperties:
    """Test GPUProperties dataclass."""
    
    def test_gpu_configs_defined(self):
        """Test that GPU configurations are properly defined."""
        assert GPUModel.RTX_3060TI in GPU_CONFIGS
        assert GPUModel.RTX_5070TI in GPU_CONFIGS
        assert GPUModel.UNKNOWN in GPU_CONFIGS
    
    def test_rtx_3060ti_config(self):
        """Test RTX 3060Ti configuration."""
        config = GPU_CONFIGS[GPUModel.RTX_3060TI]
        assert config.cuda_cores == 12288
        assert config.vram_gb == 24
        assert config.compute_capability == (8, 9)
        assert config.memory_bandwidth_gbps == 608.0
        assert config.recommended_batch_size == 2048
        assert config.max_batch_size == 8192
        assert config.memory_pool_size_mb == 20480
    
    def test_rtx_5070ti_config(self):
        """Test RTX 5070Ti configuration."""
        config = GPU_CONFIGS[GPUModel.RTX_5070TI]
        assert config.cuda_cores == 6144
        assert config.vram_gb == 16
        assert config.compute_capability == (8, 9)
        assert config.memory_bandwidth_gbps == 448.0
        assert config.recommended_batch_size == 1024
        assert config.max_batch_size == 4096
        assert config.memory_pool_size_mb == 13333
    
    def test_unknown_config(self):
        """Test unknown GPU configuration (conservative defaults)."""
        config = GPU_CONFIGS[GPUModel.UNKNOWN]
        assert config.cuda_cores == 0
        assert config.vram_gb == 0
        assert config.compute_capability == (0, 0)
        assert config.recommended_batch_size == 512
        assert config.max_batch_size == 2048
        assert config.memory_pool_size_mb == 8192


class TestGPUSelectionStrategy:
    """Test GPUSelectionStrategy enum."""
    
    def test_strategy_values(self):
        """Test GPUSelectionStrategy enum values."""
        assert GPUSelectionStrategy.AUTO.value == "auto"
        assert GPUSelectionStrategy.SPECIFIC.value == "specific"
        assert GPUSelectionStrategy.FIRST.value == "first"
        assert GPUSelectionStrategy.MOST_VRAM.value == "most_vram"
        assert GPUSelectionStrategy.MOST_CORES.value == "most_cores"


class TestGPUDetection:
    """Test GPU detection functionality."""
    
    @patch('src.core.gpu_utils.HAS_GPU', True)
    @patch('src.core.gpu_utils.xp')
    def test_detect_rtx_3060ti_by_name(self, mock_xp):
        """Test detection of RTX 3060Ti by device name."""
        mock_device = Mock()
        mock_device.name = "NVIDIA GeForce RTX 3060 Ti"
        mock_device.mem_info = (24 * 1024**3, 20 * 1024**3)
        mock_device.compute_capability = (8, 9)
        
        # Mock cupy module
        mock_cupy = MagicMock()
        mock_cupy.cuda.Device.return_value = mock_device
        
        with patch.dict('sys.modules', {'cupy': mock_cupy}):
            model = _detect_gpu_model(0)
            assert model == GPUModel.RTX_3060TI
    
    @patch('src.core.gpu_utils.HAS_GPU', True)
    @patch('src.core.gpu_utils.xp')
    def test_detect_rtx_5070ti_by_name(self, mock_xp):
        """Test detection of RTX 5070Ti by device name."""
        mock_device = Mock()
        mock_device.name = "NVIDIA GeForce RTX 5070 Ti"
        mock_device.mem_info = (16 * 1024**3, 12 * 1024**3)
        mock_device.compute_capability = (8, 9)
        
        # Mock cupy module
        mock_cupy = MagicMock()
        mock_cupy.cuda.Device.return_value = mock_device
        
        with patch.dict('sys.modules', {'cupy': mock_cupy}):
            model = _detect_gpu_model(0)
            assert model == GPUModel.RTX_5070TI
    
    @patch('src.core.gpu_utils.HAS_GPU', True)
    @patch('src.core.gpu_utils.xp')
    def test_detect_rtx_3060ti_by_memory(self, mock_xp):
        """Test detection of RTX 3060Ti by memory size (heuristic)."""
        mock_device = Mock()
        mock_device.name = "Unknown GPU"
        mock_device.mem_info = (24 * 1024**3, 20 * 1024**3)
        mock_device.compute_capability = (8, 9)
        
        # Mock cupy module
        mock_cupy = MagicMock()
        mock_cupy.cuda.Device.return_value = mock_device
        
        with patch.dict('sys.modules', {'cupy': mock_cupy}):
            model = _detect_gpu_model(0)
            assert model == GPUModel.RTX_3060TI
    
    @patch('src.core.gpu_utils.HAS_GPU', True)
    @patch('src.core.gpu_utils.xp')
    def test_detect_rtx_5070ti_by_memory(self, mock_xp):
        """Test detection of RTX 5070Ti by memory size (heuristic)."""
        mock_device = Mock()
        mock_device.name = "Unknown GPU"
        mock_device.mem_info = (16 * 1024**3, 12 * 1024**3)
        mock_device.compute_capability = (8, 9)
        
        # Mock cupy module
        mock_cupy = MagicMock()
        mock_cupy.cuda.Device.return_value = mock_device
        
        with patch.dict('sys.modules', {'cupy': mock_cupy}):
            model = _detect_gpu_model(0)
            assert model == GPUModel.RTX_5070TI


class TestGPUSelection:
    """Test GPU selection logic."""
    
    def test_select_first_gpu(self):
        """Test selecting the first available GPU."""
        gpu1 = DetectedGPU(
            device_id=0,
            model=GPUModel.RTX_5070TI,
            properties=GPU_CONFIGS[GPUModel.RTX_5070TI],
            total_memory_mb=16384,
            free_memory_mb=12000
        )
        gpu2 = DetectedGPU(
            device_id=1,
            model=GPUModel.RTX_3060TI,
            properties=GPU_CONFIGS[GPUModel.RTX_3060TI],
            total_memory_mb=24576,
            free_memory_mb=20000
        )
        
        with patch('src.core.gpu_utils._detected_gpus', [gpu1, gpu2]):
            selected = _select_gpu(GPUSelectionStrategy.FIRST)
            assert selected is not None
            assert selected.device_id == 0
    
    def test_select_most_vram(self):
        """Test selecting GPU with most VRAM."""
        gpu1 = DetectedGPU(
            device_id=0,
            model=GPUModel.RTX_5070TI,
            properties=GPU_CONFIGS[GPUModel.RTX_5070TI],
            total_memory_mb=16384,
            free_memory_mb=12000
        )
        gpu2 = DetectedGPU(
            device_id=1,
            model=GPUModel.RTX_3060TI,
            properties=GPU_CONFIGS[GPUModel.RTX_3060TI],
            total_memory_mb=24576,
            free_memory_mb=20000
        )
        
        with patch('src.core.gpu_utils._detected_gpus', [gpu1, gpu2]):
            selected = _select_gpu(GPUSelectionStrategy.MOST_VRAM)
            assert selected is not None
            assert selected.device_id == 1
            assert selected.model == GPUModel.RTX_3060TI
    
    def test_select_most_cores(self):
        """Test selecting GPU with most CUDA cores."""
        gpu1 = DetectedGPU(
            device_id=0,
            model=GPUModel.RTX_5070TI,
            properties=GPU_CONFIGS[GPUModel.RTX_5070TI],
            total_memory_mb=16384,
            free_memory_mb=12000
        )
        gpu2 = DetectedGPU(
            device_id=1,
            model=GPUModel.RTX_3060TI,
            properties=GPU_CONFIGS[GPUModel.RTX_3060TI],
            total_memory_mb=24576,
            free_memory_mb=20000
        )
        
        with patch('src.core.gpu_utils._detected_gpus', [gpu1, gpu2]):
            selected = _select_gpu(GPUSelectionStrategy.MOST_CORES)
            assert selected is not None
            assert selected.device_id == 1
            assert selected.model == GPUModel.RTX_3060TI
    
    def test_auto_select_rtx_3060ti(self):
        """Test auto selection prefers RTX 3060Ti."""
        gpu1 = DetectedGPU(
            device_id=0,
            model=GPUModel.RTX_5070TI,
            properties=GPU_CONFIGS[GPUModel.RTX_5070TI],
            total_memory_mb=16384,
            free_memory_mb=12000
        )
        gpu2 = DetectedGPU(
            device_id=1,
            model=GPUModel.RTX_3060TI,
            properties=GPU_CONFIGS[GPUModel.RTX_3060TI],
            total_memory_mb=24576,
            free_memory_mb=20000
        )
        
        with patch('src.core.gpu_utils._detected_gpus', [gpu1, gpu2]):
            selected = _select_gpu(GPUSelectionStrategy.AUTO)
            assert selected is not None
            assert selected.model == GPUModel.RTX_3060TI
    
    def test_select_specific_gpu(self):
        """Test selecting a specific GPU by ID."""
        gpu1 = DetectedGPU(
            device_id=0,
            model=GPUModel.RTX_5070TI,
            properties=GPU_CONFIGS[GPUModel.RTX_5070TI],
            total_memory_mb=16384,
            free_memory_mb=12000
        )
        gpu2 = DetectedGPU(
            device_id=1,
            model=GPUModel.RTX_3060TI,
            properties=GPU_CONFIGS[GPUModel.RTX_3060TI],
            total_memory_mb=24576,
            free_memory_mb=20000
        )
        
        with patch('src.core.gpu_utils._detected_gpus', [gpu1, gpu2]):
            selected = _select_gpu(GPUSelectionStrategy.SPECIFIC, specific_id=1)
            assert selected is not None
            assert selected.device_id == 1


class TestMultiGPU:
    """Test multi-GPU functionality."""
    
    def test_enable_multi_gpu_all_devices(self):
        """Test enabling multi-GPU with all available devices."""
        gpu1 = DetectedGPU(
            device_id=0,
            model=GPUModel.RTX_5070TI,
            properties=GPU_CONFIGS[GPUModel.RTX_5070TI],
            total_memory_mb=16384,
            free_memory_mb=12000
        )
        gpu2 = DetectedGPU(
            device_id=1,
            model=GPUModel.RTX_3060TI,
            properties=GPU_CONFIGS[GPUModel.RTX_3060TI],
            total_memory_mb=24576,
            free_memory_mb=20000
        )
        
        with patch('src.core.gpu_utils._detected_gpus', [gpu1, gpu2]):
            with patch('src.core.gpu_utils.HAS_GPU', True):
                enable_multi_gpu()
                assert is_multi_gpu_enabled()
                assert get_active_gpu_ids() == [0, 1]
    
    def test_enable_multi_gpu_specific_devices(self):
        """Test enabling multi-GPU with specific devices."""
        gpu1 = DetectedGPU(
            device_id=0,
            model=GPUModel.RTX_5070TI,
            properties=GPU_CONFIGS[GPUModel.RTX_5070TI],
            total_memory_mb=16384,
            free_memory_mb=12000
        )
        gpu2 = DetectedGPU(
            device_id=1,
            model=GPUModel.RTX_3060TI,
            properties=GPU_CONFIGS[GPUModel.RTX_3060TI],
            total_memory_mb=24576,
            free_memory_mb=20000
        )
        
        with patch('src.core.gpu_utils._detected_gpus', [gpu1, gpu2]):
            with patch('src.core.gpu_utils.HAS_GPU', True):
                enable_multi_gpu([0])
                assert is_multi_gpu_enabled() is False  # Only 1 device
                assert get_active_gpu_ids() == [0]
    
    def test_disable_multi_gpu(self):
        """Test disabling multi-GPU mode."""
        gpu1 = DetectedGPU(
            device_id=0,
            model=GPUModel.RTX_5070TI,
            properties=GPU_CONFIGS[GPUModel.RTX_5070TI],
            total_memory_mb=16384,
            free_memory_mb=12000
        )
        gpu2 = DetectedGPU(
            device_id=1,
            model=GPUModel.RTX_3060TI,
            properties=GPU_CONFIGS[GPUModel.RTX_3060TI],
            total_memory_mb=24576,
            free_memory_mb=20000
        )
        
        with patch('src.core.gpu_utils._detected_gpus', [gpu1, gpu2]):
            with patch('src.core.gpu_utils.HAS_GPU', True):
                with patch('src.core.gpu_utils._selected_gpu', gpu1):
                    enable_multi_gpu()
                    assert is_multi_gpu_enabled()
                    
                    disable_multi_gpu()
                    assert not is_multi_gpu_enabled()
                    assert get_active_gpu_ids() == []


class TestGPUTracker:
    """Test GPUTracker class."""
    
    def test_tracker_initialization_rtx_3060ti(self):
        """Test GPUTracker initialization with RTX 3060Ti."""
        gpu = DetectedGPU(
            device_id=0,
            model=GPUModel.RTX_3060TI,
            properties=GPU_CONFIGS[GPUModel.RTX_3060TI],
            total_memory_mb=24576,
            free_memory_mb=20000
        )
        
        with patch('src.core.gpu_utils._selected_gpu', gpu):
            tracker = GPUTracker("TestComponent")
            assert tracker.cuda_cores == 12288
            assert tracker.vram_gb == 24
            assert tracker.recommended_batch_size == 2048
            assert tracker.max_batch_size == 8192
    
    def test_tracker_initialization_rtx_5070ti(self):
        """Test GPUTracker initialization with RTX 5070Ti."""
        gpu = DetectedGPU(
            device_id=0,
            model=GPUModel.RTX_5070TI,
            properties=GPU_CONFIGS[GPUModel.RTX_5070TI],
            total_memory_mb=16384,
            free_memory_mb=12000
        )
        
        with patch('src.core.gpu_utils._selected_gpu', gpu):
            tracker = GPUTracker("TestComponent")
            assert tracker.cuda_cores == 6144
            assert tracker.vram_gb == 16
            assert tracker.recommended_batch_size == 1024
            assert tracker.max_batch_size == 4096
    
    def test_tracker_optimal_batch_size_rtx_3060ti(self):
        """Test optimal batch size calculation for RTX 3060Ti."""
        gpu = DetectedGPU(
            device_id=0,
            model=GPUModel.RTX_3060TI,
            properties=GPU_CONFIGS[GPUModel.RTX_3060TI],
            total_memory_mb=24576,
            free_memory_mb=20000
        )
        
        with patch('src.core.gpu_utils._selected_gpu', gpu):
            tracker = GPUTracker("TestComponent")
            # RTX 3060Ti should double the base batch size
            assert tracker.get_optimal_batch_size(512) == 1024
            # But capped at max_batch_size
            assert tracker.get_optimal_batch_size(5000) == 8192
    
    def test_tracker_optimal_batch_size_rtx_5070ti(self):
        """Test optimal batch size calculation for RTX 5070Ti."""
        gpu = DetectedGPU(
            device_id=0,
            model=GPUModel.RTX_5070TI,
            properties=GPU_CONFIGS[GPUModel.RTX_5070TI],
            total_memory_mb=16384,
            free_memory_mb=12000
        )
        
        with patch('src.core.gpu_utils._selected_gpu', gpu):
            tracker = GPUTracker("TestComponent")
            # RTX 5070Ti should use base batch size
            assert tracker.get_optimal_batch_size(512) == 512
            # But capped at max_batch_size
            assert tracker.get_optimal_batch_size(5000) == 4096


class TestConfigurationIntegration:
    """Test integration with configuration file."""
    
    def test_load_gpu_config(self):
        """Test loading GPU configuration from config file."""
        import json
        
        with open('config/eternal_crusade_config.json', 'r') as f:
            config = json.load(f)
        
        assert 'gpu' in config
        gpu_config = config['gpu']
        
        assert 'enabled' in gpu_config
        assert 'selection_strategy' in gpu_config
        assert 'multi_gpu_enabled' in gpu_config
        assert 'gpu_profiles' in gpu_config
        
        assert 'RTX_3060TI' in gpu_config['gpu_profiles']
        assert 'RTX_5070TI' in gpu_config['gpu_profiles']
        assert 'default' in gpu_config['gpu_profiles']
        
        # Verify RTX 3060Ti profile
        rtx_3060ti = gpu_config['gpu_profiles']['RTX_3060TI']
        assert rtx_3060ti['cuda_cores'] == 12288
        assert rtx_3060ti['vram_gb'] == 24
        assert rtx_3060ti['recommended_batch_size'] == 2048
        
        # Verify RTX 5070Ti profile
        rtx_5070ti = gpu_config['gpu_profiles']['RTX_5070TI']
        assert rtx_5070ti['cuda_cores'] == 6144
        assert rtx_5070ti['vram_gb'] == 16
        assert rtx_5070ti['recommended_batch_size'] == 1024


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
