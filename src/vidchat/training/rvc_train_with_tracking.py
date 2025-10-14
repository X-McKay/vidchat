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
    # Load config
    try:
        config = load_config()
        rvc_dir = config.paths.rvc_dir
    except:
        rvc_dir = Path.home() / "RVC"

    exp_dir = rvc_dir / "logs" / experiment_name
    log_file = exp_dir / "train.log"

    # Check if experiment directory exists
    if not exp_dir.exists():
        print(f"❌ Experiment directory not found: {exp_dir}")
        print("Run preprocessing first!")
        return

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
    ]

    env = os.environ.copy()
    if not gpu:
        env["CUDA_VISIBLE_DEVICES"] = ""

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
