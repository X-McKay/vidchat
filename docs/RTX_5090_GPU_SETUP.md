# RTX 5090 GPU Setup for VidChat

## Issue
RTX 5090 (Blackwell architecture) requires CUDA 12.8 and PyTorch 2.9.0+ with sm_120 support.

Older PyTorch versions show this error:
```
NVIDIA GeForce RTX 5090 with CUDA capability sm_120 is not compatible with the current PyTorch installation.
The current PyTorch install supports CUDA capabilities sm_50 sm_60 sm_70 sm_75 sm_80 sm_86 sm_90.
```

## Solution

Install PyTorch 2.9.0+ with CUDA 12.8:

```bash
~/.local/share/mise/installs/python/3.10.19/bin/python3 -m pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

## Verification

Test GPU functionality:

```bash
python3 -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA: {torch.version.cuda}')
print(f'GPU: {torch.cuda.get_device_name(0)}')
print(f'Compute Cap: {torch.cuda.get_device_capability(0)}')
x = torch.randn(1000, 1000).cuda()
y = torch.randn(1000, 1000).cuda()
z = x @ y
print(f'✓ GPU Working: {z.sum().item():.2f}')
"
```

Expected output:
```
PyTorch: 2.9.0+cu128
CUDA: 12.8
GPU: NVIDIA GeForce RTX 5090
Compute Cap: (12, 0)
✓ GPU Working: [some number]
```

## Training with GPU

Now you can use `--use-gpu` flag:

```bash
# Train RVC model with GPU acceleration
uv run vidchat-cli train-model --epochs 500 --batch-size 8 --use-gpu
```

GPU training is **10-20x faster** than CPU:
- CPU: ~8-12 hours for 500 epochs
- GPU (RTX 5090): ~30-60 minutes for 500 epochs

## References

- [PyTorch GitHub Issue #159207](https://github.com/pytorch/pytorch/issues/159207)
- [CUDA 12.8 Release Notes](https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/)
