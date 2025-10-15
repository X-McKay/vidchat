"""RVC training with MLflow experiment tracking.

This script wraps the RVC training process and adds MLflow logging
to track experiments, parameters, metrics, and artifacts.
"""

import os
import sys
import subprocess
import re
from pathlib import Path
from typing import Optional
import time

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

try:
    from vidchat.training.mlflow_tracker import create_rvc_tracker
    from vidchat.utils.config_loader import load_config
except ImportError:
    print("Warning: Could not import tracking modules. MLflow tracking disabled.")
    create_rvc_tracker = None


def parse_log_metrics(log_line: str) -> Optional[dict]:
    """Parse metrics from RVC training log line.

    Example log format:
    INFO:experiment:[epoch 5] loss_disc=1.234, loss_gen=2.345, loss_fm=3.456, loss_mel=4.567
    """
    # Pattern to match epoch and metrics
    epoch_match = re.search(r'\[epoch (\d+)\]', log_line)
    if not epoch_match:
        return None

    epoch = int(epoch_match.group(1))
    metrics = {}

    # Extract all metrics (loss_* = value)
    metric_pattern = r'(\w+)=([\d.]+)'
    for match in re.finditer(metric_pattern, log_line):
        key, value = match.groups()
        if key.startswith('loss_') or key in ['lr', 'grad_norm']:
            metrics[key] = float(value)

    if metrics:
        return {'epoch': epoch, 'metrics': metrics}
    return None


def tail_and_log_metrics(
    log_file: Path,
    tracker,
    stop_event=None,
):
    """Tail log file and log metrics to MLflow in real-time.

    Args:
        log_file: Path to training log file
        tracker: MLflowTracker instance
        stop_event: Optional threading.Event to signal stop
    """
    print(f"📊 Monitoring training log: {log_file}")

    last_position = 0
    while stop_event is None or not stop_event.is_set():
        if not log_file.exists():
            time.sleep(1)
            continue

        try:
            with open(log_file, 'r') as f:
                f.seek(last_position)
                lines = f.readlines()
                last_position = f.tell()

                for line in lines:
                    # Parse and log metrics
                    parsed = parse_log_metrics(line)
                    if parsed:
                        epoch = parsed['epoch']
                        metrics = parsed['metrics']
                        tracker.log_metrics(metrics, step=epoch)
                        print(f"  Epoch {epoch}: {metrics}")

        except Exception as e:
            print(f"Warning: Error reading log: {e}")

        time.sleep(2)  # Poll every 2 seconds


def train_rvc_with_tracking(
    experiment_name: str,
    epochs: int = 300,
    batch_size: int = 4,
    save_freq: int = 10,
    gpu: bool = False,
):
    """Train RVC model with MLflow tracking.

    Args:
        experiment_name: Name of the experiment (voice name)
        epochs: Number of training epochs
        batch_size: Batch size for training
        save_freq: Save checkpoint every N epochs
        gpu: Use GPU if available
    """
    # Use RVC from project's external directory
    project_root = Path(__file__).resolve().parents[3]
    rvc_dir = project_root / "external" / "RVC"

    exp_dir = rvc_dir / "logs" / experiment_name
    log_file = exp_dir / "train.log"

    # Check if training data exists in VidChat's data directory
    project_root = Path(__file__).resolve().parents[3]
    vidchat_data_dir = project_root / ".data" / "voice_data" / experiment_name

    if not vidchat_data_dir.exists() or not list(vidchat_data_dir.glob("*.wav")):
        print(f"❌ Training data not found: {vidchat_data_dir}")
        print("Run: vidchat-cli prepare-data")
        return

    # Create RVC experiment directory structure
    exp_dir.mkdir(parents=True, exist_ok=True)
    gt_wavs_dir = exp_dir / "0_gt_wavs"
    gt_wavs_dir.mkdir(exist_ok=True)

    # Copy prepared audio files to RVC directory
    print(f"\n📂 Copying audio files to RVC directory...")
    wav_files = list(vidchat_data_dir.glob("*.wav"))
    print(f"   Found {len(wav_files)} audio files")

    import shutil
    for wav_file in wav_files:
        dest = gt_wavs_dir / wav_file.name
        if not dest.exists():
            shutil.copy2(wav_file, dest)

    print(f"   ✓ Copied to: {gt_wavs_dir}")

    # Run RVC preprocessing pipeline
    print(f"\n🔧 Running RVC preprocessing...")
    python_cmd = str(Path.home() / ".local/share/mise/installs/python/3.10.19/bin/python3")

    # Step 1: Preprocess audio (resample and slice)
    print("   1/5 Preprocessing audio...")
    preprocess_cmd = [
        python_cmd,
        str(rvc_dir / "infer/modules/train/preprocess.py"),
        str(gt_wavs_dir),
        "40000",  # Sample rate
        str(os.cpu_count() or 4),  # Number of CPU cores
        str(exp_dir),
        "False",  # noparallel
        "3.7",  # Segment length
    ]

    result = subprocess.run(preprocess_cmd, cwd=rvc_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ❌ Preprocessing failed:")
        print(result.stderr)
        return
    print(f"   ✓ Preprocessing complete")

    # Step 2: Extract pitch (f0)
    print("   2/5 Extracting pitch (f0)...")
    f0_extract_cmd = [
        python_cmd,
        str(rvc_dir / "infer/modules/train/extract/extract_f0_print.py"),
        str(exp_dir),
        str(os.cpu_count() or 4),  # Number of processes
        "rmvpe",  # F0 extraction method (rmvpe is most accurate)
    ]

    result = subprocess.run(f0_extract_cmd, cwd=rvc_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ❌ Pitch extraction failed:")
        print(result.stderr)
        return
    print(f"   ✓ Pitch extraction complete")

    # Step 3: Extract features (using patched wrapper for PyTorch 2.6 compatibility)
    print("   3/5 Extracting features...")
    patched_extract_script = project_root / "src" / "vidchat" / "training" / "extract_features_patched.py"
    extract_cmd = [
        python_cmd,
        str(patched_extract_script),
        "cpu",  # Device
        "1",  # Number of processes
        "0",  # GPU ID (ignored for CPU)
        str(exp_dir),
        "v2",  # Model version
        "False",  # Use diff
    ]

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = ""

    result = subprocess.run(extract_cmd, cwd=rvc_dir, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"   ❌ Feature extraction failed:")
        print(result.stderr)
        return
    print(f"   ✓ Feature extraction complete")

    # Step 4: Create filelist.txt
    print("   4/5 Creating filelist...")
    filelist_path = exp_dir / "filelist.txt"
    gt_wavs_dir = exp_dir / "0_gt_wavs"
    f0_dir = exp_dir / "2a_f0"
    f0nsf_dir = exp_dir / "2b-f0nsf"
    feature_dir = exp_dir / "3_feature768"

    with open(filelist_path, "w", encoding="utf-8") as f:
        # List all processed audio files with their pitch and feature files
        # Format: gt_wav|f0|f0nsf|feature|speaker_id
        wav_files = sorted(gt_wavs_dir.glob("*.wav"))
        for wav_file in wav_files:
            base_name = wav_file.stem  # filename without extension
            f0_file = f0_dir / f"{base_name}.wav.npy"
            f0nsf_file = f0nsf_dir / f"{base_name}.wav.npy"
            feature_file = feature_dir / f"{base_name}.npy"

            # Use relative paths from RVC directory
            rel_gt = f"logs/{experiment_name}/0_gt_wavs/{wav_file.name}"
            rel_f0 = f"logs/{experiment_name}/2a_f0/{base_name}.wav.npy"
            rel_f0nsf = f"logs/{experiment_name}/2b-f0nsf/{base_name}.wav.npy"
            rel_feature = f"logs/{experiment_name}/3_feature768/{base_name}.npy"

            f.write(f"{rel_gt}|{rel_f0}|{rel_f0nsf}|{rel_feature}|0\n")

    print(f"   ✓ Created filelist with {len(wav_files)} files")

    # Step 5: Create config.json
    print("   5/5 Creating training config...")
    import json
    config_data = {
        "train": {
            "log_interval": 200,
            "eval_interval": 800,
            "seed": 1234,
            "epochs": epochs,
            "learning_rate": 0.0001,
            "betas": [0.8, 0.99],
            "eps": 1e-9,
            "batch_size": batch_size,
            "fp16_run": False,
            "lr_decay": 0.999875,
            "segment_size": 17280,
            "init_lr_ratio": 1,
            "warmup_epochs": 0,
            "c_mel": 45,
            "c_kl": 1.0
        },
        "data": {
            "max_wav_value": 32768.0,
            "sampling_rate": 40000,
            "filter_length": 2048,
            "hop_length": 400,
            "win_length": 2048,
            "n_mel_channels": 125,
            "mel_fmin": 0.0,
            "mel_fmax": None
        },
        "model": {
            "inter_channels": 192,
            "hidden_channels": 192,
            "filter_channels": 768,
            "n_heads": 2,
            "n_layers": 6,
            "kernel_size": 3,
            "p_dropout": 0.0,
            "resblock": "1",
            "resblock_kernel_sizes": [3, 7, 11],
            "resblock_dilation_sizes": [[1, 3, 5], [1, 3, 5], [1, 3, 5]],
            "upsample_rates": [10, 10, 2, 2],
            "upsample_initial_channel": 512,
            "upsample_kernel_sizes": [16, 16, 4, 4],
            "spk_embed_dim": 109,
            "gin_channels": 256,
            "sr": "40k"
        },
        "spk": {experiment_name: 0}
    }

    config_file = exp_dir / "config.json"
    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=2)
    print(f"   ✓ Config created: {config_file}")
    print(f"   ✓ RVC preprocessing finished!\n")

    # Create MLflow tracker
    if create_rvc_tracker:
        tracker = create_rvc_tracker(experiment_name, epochs, batch_size)
    else:
        tracker = None
        print("⚠️  MLflow tracking disabled")

    # Set up training command
    python_cmd = str(Path.home() / ".local/share/mise/installs/python/3.10.19/bin/python3")
    train_script = rvc_dir / "infer/modules/train/train.py"

    cmd = [
        python_cmd,
        str(train_script),
        "-e", experiment_name,
        "-sr", "40k",
        "-f0", "1",
        "-bs", str(batch_size),
        "-g", "cpu" if not gpu else "0",
        "-te", str(epochs),
        "-se", str(save_freq),
        "-pg", str(rvc_dir / "assets/pretrained_v2/f0G40k.pth"),
        "-pd", str(rvc_dir / "assets/pretrained_v2/f0D40k.pth"),
        "-l", "1",
        "-c", "0",
        "-v", "v2",  # Model version
    ]

    env = os.environ.copy()
    if not gpu:
        env["CUDA_VISIBLE_DEVICES"] = ""
    else:
        # Enable RTX 5090 (sm_120) support via JIT compilation
        env["TORCH_CUDA_ARCH_LIST"] = "9.0+PTX"  # Use PTX for forward compatibility
        env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

    print("=" * 60)
    print("🎤 RVC Training with MLflow Tracking")
    print("=" * 60)
    print(f"Experiment: {experiment_name}")
    print(f"Epochs: {epochs}")
    print(f"Batch size: {batch_size}")
    print(f"Mode: {'GPU' if gpu else 'CPU'}")
    print(f"Save frequency: Every {save_freq} epochs")
    print("=" * 60)

    # Start MLflow run
    if tracker:
        with tracker.start_run():
            # Log parameters
            tracker.log_params({
                "voice_name": experiment_name,
                "epochs": epochs,
                "batch_size": batch_size,
                "save_frequency": save_freq,
                "sample_rate": "40k",
                "use_f0": True,
                "mode": "GPU" if gpu else "CPU",
            })

            # Log tags
            tracker.set_tags({
                "model_type": "RVC",
                "version": "v2",
                "training_script": "rvc_train_with_tracking.py",
            })

            print(f"\n📊 MLflow tracking enabled")
            print(f"   Tracking URI: {tracker.get_tracking_uri()}")
            print(f"   View UI: mlflow ui --backend-store-uri {tracker.get_tracking_uri()}")
            print()

            # Start training process
            print("🚀 Starting training...")
            with open(log_file, "w") as f:
                process = subprocess.Popen(
                    cmd,
                    cwd=rvc_dir,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    env=env,
                )

            print(f"✓ Training started (PID: {process.pid})")
            print(f"📝 Logging to: {log_file}")
            print("\nMonitoring metrics (press Ctrl+C to stop monitoring, training continues)...")

            # Monitor and log metrics
            try:
                import threading
                stop_event = threading.Event()

                monitor_thread = threading.Thread(
                    target=tail_and_log_metrics,
                    args=(log_file, tracker, stop_event),
                    daemon=True,
                )
                monitor_thread.start()

                # Wait for process to complete or user interrupt
                process.wait()
                stop_event.set()
                monitor_thread.join(timeout=5)

            except KeyboardInterrupt:
                print("\n⚠️  Monitoring stopped (training continues in background)")

            # Log final artifacts
            print("\n📦 Logging artifacts...")
            if exp_dir.exists():
                # Log checkpoints
                checkpoints = list(exp_dir.glob("G_*.pth"))
                if checkpoints:
                    tracker.log_artifact(str(checkpoints[-1]))
                    print(f"   Logged checkpoint: {checkpoints[-1].name}")

                # Log config
                config_file = exp_dir / "config.json"
                if config_file.exists():
                    tracker.log_artifact(str(config_file))
                    print(f"   Logged config: {config_file.name}")

            print(f"\n✓ Training complete!")
            print(f"📊 View results: mlflow ui")

    else:
        # Train without MLflow
        print("\n🚀 Starting training (no tracking)...")
        with open(log_file, "w") as f:
            process = subprocess.run(cmd, cwd=rvc_dir, stdout=f, stderr=subprocess.STDOUT, env=env)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train RVC model with MLflow tracking")
    parser.add_argument("experiment", type=str, help="Experiment name (voice name)")
    parser.add_argument("--epochs", "-e", type=int, default=300, help="Number of epochs")
    parser.add_argument("--batch-size", "-b", type=int, default=4, help="Batch size")
    parser.add_argument("--save-freq", "-s", type=int, default=10, help="Save frequency (epochs)")
    parser.add_argument("--gpu", "-g", action="store_true", help="Use GPU if available")

    args = parser.parse_args()

    train_rvc_with_tracking(
        experiment_name=args.experiment,
        epochs=args.epochs,
        batch_size=args.batch_size,
        save_freq=args.save_freq,
        gpu=args.gpu,
    )
