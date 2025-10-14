"""MLflow tracking for RVC training experiments.

This module provides a simple wrapper for MLflow experiment tracking,
making it easy to log metrics, parameters, and artifacts during training.
"""

import mlflow
from pathlib import Path
from typing import Any, Dict, Optional
from contextlib import contextmanager


class MLflowTracker:
    """MLflow experiment tracker for RVC voice training."""

    def __init__(
        self,
        experiment_name: str,
        tracking_uri: Optional[str] = None,
        run_name: Optional[str] = None,
    ):
        """Initialize MLflow tracker.

        Args:
            experiment_name: Name of the experiment (e.g., "rvc-voice-training")
            tracking_uri: MLflow tracking server URI. If None, uses local file store.
            run_name: Optional name for the run (e.g., "robg-300epochs")
        """
        self.experiment_name = experiment_name
        self.run_name = run_name

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
            yield self

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
