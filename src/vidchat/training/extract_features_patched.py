"""Patched feature extraction wrapper that fixes PyTorch 2.6 weights_only issue."""
import sys
from pathlib import Path

# Patch torch.load before importing anything else
import torch
original_torch_load = torch.load

def patched_torch_load(*args, **kwargs):
    """Wrapper for torch.load that sets weights_only=False for compatibility."""
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return original_torch_load(*args, **kwargs)

torch.load = patched_torch_load

# Now import and run the RVC extraction script
# Find project root and use external/RVC
current = Path(__file__).resolve()
project_root = current.parents[3]  # Go up to project root
rvc_dir = project_root / "external" / "RVC"
sys.path.insert(0, str(rvc_dir))

# Import the actual extraction script
import importlib.util
spec = importlib.util.spec_from_file_location(
    "extract_feature_print",
    rvc_dir / "infer/modules/train/extract_feature_print.py"
)
extract_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extract_module)
