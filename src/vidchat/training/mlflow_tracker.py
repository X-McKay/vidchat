"""MLflow tracking for RVC training experiments.

This module provides a simple wrapper for MLflow experiment tracking,
making it easy to log metrics, parameters, and artifacts during training.

Includes system metrics monitoring (GPU/CPU, memory) and model checkpoint logging.
"""

import mlflow
from pathlib import Path
from typing import Any, Dict, Optional
from contextlib import contextmanager
import time
import psutil
import threading


class MLflowTracker:
    """MLflow experiment tracker for RVC voice training with system metrics."""

    def __init__(
        self,
        experiment_name: str,
        tracking_uri: Optional[str] = None,
        run_name: Optional[str] = None,
        monitor_system: bool = True,
        monitor_interval: int = 30,
    ):
        """Initialize MLflow tracker.

        Args:
            experiment_name: Name of the experiment (e.g., "rvc-voice-training")
            tracking_uri: MLflow tracking server URI. If None, uses local file store.
            run_name: Optional name for the run (e.g., "robg-300epochs")
            monitor_system: Enable system metrics monitoring (GPU, CPU, memory)
            monitor_interval: Interval in seconds between system metric samples
        """
        self.experiment_name = experiment_name
        self.run_name = run_name
        self.monitor_system = monitor_system
        self.monitor_interval = monitor_interval
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()
        self._step_counter = 0

        # Set up tracking URI (default to local file store in .data/mlflow)
        if tracking_uri is None:
            from vidchat.utils.config_loader import get_project_root
            project_root = get_project_root()
            tracking_uri = (project_root / ".data" / "mlruns").as_uri()

        mlflow.set_tracking_uri(tracking_uri)

        # Create or get experiment
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(experiment_name)
            else:
                experiment_id = experiment.experiment_id
            self.experiment_id = experiment_id
        except Exception as e:
            print(f"Warning: Could not set up MLflow experiment: {e}")
            self.experiment_id = None

        # Detect GPU availability
        self.has_gpu = False
        try:
            import torch
            self.has_gpu = torch.cuda.is_available()
            if self.has_gpu:
                self.gpu_name = torch.cuda.get_device_name(0)
        except ImportError:
            pass

    def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect current system metrics (CPU, memory, GPU)."""
        metrics = {}

        # CPU and Memory
        metrics["system/cpu_percent"] = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        metrics["system/memory_percent"] = memory.percent
        metrics["system/memory_used_gb"] = memory.used / (1024**3)

        # GPU metrics if available
        if self.has_gpu:
            try:
                import torch
                if torch.cuda.is_available():
                    metrics["system/gpu_memory_allocated_gb"] = torch.cuda.memory_allocated() / (1024**3)
                    metrics["system/gpu_memory_reserved_gb"] = torch.cuda.memory_reserved() / (1024**3)
                    # Try to get GPU utilization
                    try:
                        import pynvml
                        pynvml.nvmlInit()
                        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                        metrics["system/gpu_utilization_percent"] = util.gpu
                        pynvml.nvmlShutdown()
                    except:
                        pass  # pynvml not available
            except:
                pass

        return metrics

    def _monitor_system_loop(self):
        """Background thread loop for system monitoring."""
        while not self._stop_monitoring.is_set():
            try:
                metrics = self._collect_system_metrics()
                self.log_metrics(metrics, step=self._step_counter)
                self._step_counter += 1
            except Exception as e:
                print(f"Warning: System monitoring error: {e}")

            # Wait for next sample
            self._stop_monitoring.wait(self.monitor_interval)

    def start_system_monitoring(self):
        """Start background system metrics monitoring."""
        if self.monitor_system and self._monitoring_thread is None:
            self._stop_monitoring.clear()
            self._monitoring_thread = threading.Thread(
                target=self._monitor_system_loop,
                daemon=True
            )
            self._monitoring_thread.start()
            print("📊 System monitoring started (every {}s)".format(self.monitor_interval))

    def stop_system_monitoring(self):
        """Stop background system metrics monitoring."""
        if self._monitoring_thread is not None:
            self._stop_monitoring.set()
            self._monitoring_thread.join(timeout=5)
            self._monitoring_thread = None
            print("📊 System monitoring stopped")

    @contextmanager
    def start_run(self):
        """Start an MLflow run as a context manager.

        Usage:
            with tracker.start_run():
                tracker.log_param("learning_rate", 0.001)
                tracker.log_metric("loss", 0.5, step=1)
        """
        with mlflow.start_run(
            experiment_id=self.experiment_id,
            run_name=self.run_name,
        ):
            # Start system monitoring if enabled
            self.start_system_monitoring()

            try:
                yield self
            finally:
                # Stop system monitoring
                self.stop_system_monitoring()

    def log_param(self, key: str, value: Any):
        """Log a parameter."""
        try:
            mlflow.log_param(key, value)
        except Exception as e:
            print(f"Warning: Could not log parameter {key}: {e}")

    def log_params(self, params: Dict[str, Any]):
        """Log multiple parameters."""
        try:
            mlflow.log_params(params)
        except Exception as e:
            print(f"Warning: Could not log parameters: {e}")

    def log_metric(self, key: str, value: float, step: Optional[int] = None):
        """Log a metric."""
        try:
            mlflow.log_metric(key, value, step=step)
        except Exception as e:
            print(f"Warning: Could not log metric {key}: {e}")

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log multiple metrics."""
        try:
            mlflow.log_metrics(metrics, step=step)
        except Exception as e:
            print(f"Warning: Could not log metrics: {e}")

    def log_artifact(self, local_path: str | Path):
        """Log an artifact (file)."""
        try:
            mlflow.log_artifact(str(local_path))
        except Exception as e:
            print(f"Warning: Could not log artifact {local_path}: {e}")

    def log_artifacts(self, local_dir: str | Path):
        """Log all artifacts in a directory."""
        try:
            mlflow.log_artifacts(str(local_dir))
        except Exception as e:
            print(f"Warning: Could not log artifacts from {local_dir}: {e}")

    def log_model_checkpoint(self, checkpoint_path: str | Path, epoch: int):
        """Log a model checkpoint file.

        Args:
            checkpoint_path: Path to the checkpoint file (e.g., G_100.pth)
            epoch: Epoch number for this checkpoint
        """
        try:
            checkpoint_path = Path(checkpoint_path)
            if checkpoint_path.exists():
                # Log the checkpoint file
                mlflow.log_artifact(str(checkpoint_path), artifact_path=f"checkpoints/epoch_{epoch}")
                # Log checkpoint metadata
                file_size_mb = checkpoint_path.stat().st_size / (1024 * 1024)
                self.log_metrics({
                    f"checkpoint/epoch_{epoch}_size_mb": file_size_mb,
                }, step=epoch)
                print(f"   ✓ Logged checkpoint: {checkpoint_path.name} ({file_size_mb:.1f}MB)")
            else:
                print(f"   ⚠️  Checkpoint not found: {checkpoint_path}")
        except Exception as e:
            print(f"Warning: Could not log checkpoint {checkpoint_path}: {e}")

    def log_model_checkpoints(self, checkpoint_dir: str | Path, pattern: str = "G_*.pth"):
        """Log all model checkpoints matching a pattern.

        Args:
            checkpoint_dir: Directory containing checkpoints
            pattern: Glob pattern for checkpoint files (default: "G_*.pth")
        """
        try:
            checkpoint_dir = Path(checkpoint_dir)
            checkpoints = sorted(checkpoint_dir.glob(pattern))

            if checkpoints:
                print(f"📦 Logging {len(checkpoints)} model checkpoints...")
                for checkpoint in checkpoints:
                    # Extract epoch number from filename (e.g., G_100.pth -> 100)
                    try:
                        epoch_str = checkpoint.stem.split('_')[-1]
                        epoch = int(epoch_str)
                        self.log_model_checkpoint(checkpoint, epoch)
                    except (ValueError, IndexError):
                        # If we can't extract epoch, just log the file
                        mlflow.log_artifact(str(checkpoint), artifact_path="checkpoints")
                        print(f"   ✓ Logged checkpoint: {checkpoint.name}")
            else:
                print(f"   No checkpoints found matching '{pattern}' in {checkpoint_dir}")
        except Exception as e:
            print(f"Warning: Could not log checkpoints from {checkpoint_dir}: {e}")

    def set_tag(self, key: str, value: Any):
        """Set a tag."""
        try:
            mlflow.set_tag(key, value)
        except Exception as e:
            print(f"Warning: Could not set tag {key}: {e}")

    def set_tags(self, tags: Dict[str, Any]):
        """Set multiple tags."""
        try:
            mlflow.set_tags(tags)
        except Exception as e:
            print(f"Warning: Could not set tags: {e}")

    @staticmethod
    def get_tracking_uri() -> str:
        """Get the current MLflow tracking URI."""
        return mlflow.get_tracking_uri()

    @staticmethod
    def get_ui_url() -> str:
        """Get the URL for the MLflow UI."""
        uri = mlflow.get_tracking_uri()
        if uri.startswith("file://"):
            # Local file store - UI will be at http://localhost:5000
            return "http://localhost:5000"
        return uri


def create_rvc_tracker(
    voice_name: str,
    epochs: int,
    batch_size: int,
) -> MLflowTracker:
    """Create an MLflow tracker for RVC training.

    Args:
        voice_name: Name of the voice being trained
        epochs: Number of training epochs
        batch_size: Batch size

    Returns:
        Configured MLflowTracker instance
    """
    run_name = f"{voice_name}-{epochs}epochs-bs{batch_size}"
    tracker = MLflowTracker(
        experiment_name="rvc-voice-training",
        run_name=run_name,
    )
    return tracker


# Example usage
if __name__ == "__main__":
    # Create a tracker
    tracker = create_rvc_tracker("test_voice", 300, 4)

    # Use in a training loop
    with tracker.start_run():
        # Log training parameters
        tracker.log_params({
            "voice_name": "test_voice",
            "epochs": 300,
            "batch_size": 4,
            "learning_rate": 0.0001,
            "sample_rate": 40000,
        })

        # Log tags
        tracker.set_tags({
            "model_type": "RVC",
            "mode": "CPU",
        })

        # Simulate training loop
        for epoch in range(5):
            # Log metrics
            tracker.log_metrics({
                "loss_gen": 2.5 - epoch * 0.1,
                "loss_disc": 1.8 - epoch * 0.05,
                "loss_fm": 5.2 - epoch * 0.2,
            }, step=epoch)

        print(f"✓ Logged to MLflow")
        print(f"  Tracking URI: {tracker.get_tracking_uri()}")
        print(f"  View UI at: {tracker.get_ui_url()}")
