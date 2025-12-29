# FramePack Studio Installation Notes

## Installation Summary

**Installation Method:** Fresh venv created and packages installed via automated process
**Date:** December 29, 2025
**Python Version:** 3.13

### Installed Packages

**Core AI/ML Packages:**
- PyTorch: 2.8.0+cu128
- TorchVision: 0.23.0+cu128
- TorchAudio: 2.8.0+cu128
- Diffusers: 0.36.0
- Transformers: 4.57.3
- Accelerate: 1.12.0
- PEFT: 0.18.0

**UI & Web:**
- Gradio: 6.2.0

**Media Processing:**
- OpenCV Contrib Python: 4.12.0.88
- av: 16.0.1
- imageio: 2.37.2
- imageio-ffmpeg: 0.6.0
- decord: 0.6.0

**Upscaling/Enhancement:**
- facexlib: 0.3.0
- gfpgan: 1.3.8
- realesrgan: 0.3.0

**Utilities:**
- sentencepiece: 0.2.1
- torchsde: 0.2.6
- scipy: 1.16.3
- numpy: 2.2.6

### CUDA Configuration
- CUDA Version: 12.8
- Optimized for RTX 40xx and 50xx GPUs

### Known Issues

#### BasicSR Not Installed
BasicSR has compatibility issues with Python 3.13 and could not be installed.

**Impact:**
- Some advanced toolbox features (ESRGAN, GFPGAN, RealESRGAN) may have limited functionality
- Main FramePack Studio features should work normally

**Workaround:**
1. Use Python 3.10, 3.11, or 3.12 if BasicSR features are critical
2. Wait for BasicSR to release Python 3.13 compatible wheels

**Alternative:** You can try installing BasicSR manually later if needed:
```bash
venv\Scripts\activate
pip install basicsr --no-build-isolation
```

#### NumPy Version
- Requirements specify numpy==1.26.2 but numpy 2.2.6 was installed
- This is a newer version with better Python 3.13 support
- Most packages are compatible with NumPy 2.x

### Optional Acceleration Packages

The install script offers optional acceleration packages:

**Sage Attention:**
- Requires: triton-windows<3.4
- Significant speed improvements for RTX 40xx/50xx
- Pre-built wheels available for Python 3.10-3.12

**Flash Attention:**
- Alternative acceleration method
- Pre-built wheels available

**Note:** These may not be available for Python 3.13 yet.

### Scripts Created

1. **install_40xx_50xx.bat** - Full installation script for RTX 40xx/50xx GPUs
2. **start.bat** - Launches FramePack Studio with venv activation
3. **activate_venv.bat** - Activates venv for manual commands

### Running the Application

```bash
# Option 1: Use the start script
start.bat

# Option 2: Use the existing run script
run.bat

# Option 3: Manual
venv\Scripts\activate
python studio.py
```

### Verifying Installation

```bash
venv\Scripts\activate
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
```

Expected output:
```
PyTorch: 2.8.0+cu128
CUDA: True
```

## Troubleshooting

### If PyTorch CUDA is not detected:
1. Ensure NVIDIA drivers are up to date
2. Verify nvidia-smi shows your GPU
3. Reinstall PyTorch with CUDA 12.8

### If packages are missing:
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### Clean Reinstall:
1. Delete the `venv` folder
2. Run `install_40xx_50xx.bat` again

## Python Version Recommendation

**Recommended:** Python 3.10, 3.11, or 3.12
**Current:** Python 3.13 (newer, some packages may have limited compatibility)

If you experience issues, consider using Python 3.12 for maximum compatibility.
