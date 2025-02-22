"""
System optimization script for AI Code Translator
"""

import os
import sys
import torch
import psutil
import subprocess
from pathlib import Path

def optimize_cuda_settings():
    """Optimize CUDA settings for training."""
    if not torch.cuda.is_available():
        print("CUDA not available")
        return
        
    # Set CUDA environment variables
    os.environ['CUDA_LAUNCH_BLOCKING'] = '0'
    os.environ['CUDA_CACHE_PATH'] = str(Path.home() / '.cache' / 'torch' / 'cuda_cache')
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
    
    # Configure PyTorch settings
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    
    print("CUDA settings optimized")

def optimize_system_memory():
    """Optimize system memory settings."""
    # Get system memory info
    memory = psutil.virtual_memory()
    total_gb = memory.total / (1024 ** 3)
    
    # Calculate optimal swap file size (2x RAM for ML tasks)
    optimal_swap_gb = int(total_gb * 2)
    
    print(f"System RAM: {total_gb:.1f} GB")
    print(f"Recommended swap size: {optimal_swap_gb} GB")
    
    # Print recommendations
    print("\nSystem Recommendations:")
    print("1. Set Windows page file size:")
    print(f"   - Initial size: {int(total_gb * 1024)} MB")
    print(f"   - Maximum size: {int(optimal_swap_gb * 1024)} MB")
    print("2. Close unnecessary applications")
    print("3. Disable background services")

def optimize_gpu_settings():
    """Optimize GPU settings for ML workloads."""
    try:
        # Get NVIDIA GPU info
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        print("\nGPU Information:")
        print(result.stdout)
        
        print("\nGPU Optimization Recommendations:")
        print("1. Update NVIDIA drivers to latest version")
        print("2. Set Windows power plan to 'High Performance'")
        print("3. In NVIDIA Control Panel:")
        print("   - Set 'Power management mode' to 'Prefer maximum performance'")
        print("   - Set 'CUDA - Force P2 State' to 'Off'")
        
    except Exception as e:
        print("Could not get GPU information:", e)

def main():
    """Main optimization function."""
    print("Starting system optimization...\n")
    
    # Run optimizations
    optimize_cuda_settings()
    optimize_system_memory()
    optimize_gpu_settings()
    
    print("\nOptimization complete!")
    print("\nAdditional Recommendations:")
    print("1. Regularly monitor GPU temperature")
    print("2. Keep system and GPU drivers updated")
    print("3. Consider using a cooling pad or improving ventilation")

if __name__ == "__main__":
    main()
