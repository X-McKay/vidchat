# MLflow Experiment Tracking

VidChat uses [MLflow](https://mlflow.org/) to track voice training experiments, log metrics, and compare different training runs.

## Overview

MLflow automatically logs:
- **Parameters**: Training configuration (epochs, batch size, learning rate, etc.)
- **Metrics**: Loss values per epoch (loss_gen, loss_disc, loss_fm, etc.)
- **Artifacts**: Model checkpoints, config files
- **Tags**: Model metadata (version, mode, etc.)

## Installation

MLflow is included in the `training` extras:

```bash
# Install MLflow and training dependencies
uv sync --extra training

# Or install all extras
uv sync --all-extras
```

## Usage

### 1. Train with MLflow Tracking

Training automatically logs to MLflow:

```bash
# Standard training (with MLflow tracking)
uv run vidchat-cli train-rvc robg --epochs 300 --batch-size 4
```

All metrics, parameters, and artifacts are automatically logged to `.data/mlruns/`.

### 2. View Experiments in MLflow UI

Start the MLflow UI to visualize your experiments:

```bash
# Start MLflow UI (foreground)
uv run vidchat-cli mlflow-ui

# Or run in background
uv run vidchat-cli mlflow-ui --background

# Custom port
uv run vidchat-cli mlflow-ui --port 8080
```

Then open your browser to: [http://localhost:5000](http://localhost:5000)

### 3. Compare Experiments

In the MLflow UI you can:
- **View all runs**: See all training experiments
- **Compare metrics**: Plot loss curves across different runs
- **Search and filter**: Find runs by parameter, metric, or tag
- **Download artifacts**: Get model checkpoints and configs

## MLflow UI Features

### Run List View
- See all training runs with their parameters
- Sort by metrics (e.g., best final loss)
- Filter by tags or parameters

### Run Details
- **Parameters**: All training configuration
- **Metrics**: Interactive loss curves
- **Artifacts**: Download models and configs
- **Tags**: Model metadata

### Comparison View
- Select multiple runs to compare
- Overlay metric plots
- See parameter differences
- Identify best configurations

## Directory Structure

```
.data/
└── mlruns/                     # MLflow tracking data
    ├── 0/                      # Default experiment
    │   └── meta.yaml
    └── 1/                      # rvc-voice-training experiment
        ├── meta.yaml
        └── <run-id>/          # Individual training run
            ├── meta.yaml
            ├── metrics/       # Metric logs
            ├── params/        # Parameters
            ├── tags/          # Tags
            └── artifacts/     # Model checkpoints
```

## Example Workflow

### Training Multiple Experiments

```bash
# Experiment 1: Baseline
uv run vidchat-cli train-rvc voice1 --epochs 200 --batch-size 4

# Experiment 2: More epochs
uv run vidchat-cli train-rvc voice1 --epochs 300 --batch-size 4

# Experiment 3: Larger batch
uv run vidchat-cli train-rvc voice1 --epochs 300 --batch-size 8
```

### Comparing Results

```bash
# Start MLflow UI
uv run vidchat-cli mlflow-ui

# In browser:
# 1. Select all runs
# 2. Click "Compare"
# 3. View metric plots
# 4. Find best configuration
```

## Logged Metrics

MLflow automatically tracks these metrics during training:

- `loss_gen`: Generator loss
- `loss_disc`: Discriminator loss
- `loss_fm`: Feature matching loss
- `loss_mel`: Mel-spectrogram loss
- `loss_kl`: KL divergence loss
- `lr`: Learning rate

Each metric is logged per epoch with the step number.

## Logged Parameters

Training parameters are automatically logged:

- `voice_name`: Name of the voice
- `epochs`: Total number of epochs
- `batch_size`: Training batch size
- `learning_rate`: Initial learning rate
- `sample_rate`: Audio sample rate (40k)
- `use_f0`: Whether F0 (pitch) features are used
- `mode`: Training mode (CPU/GPU)

## Logged Artifacts

After training completes, these artifacts are logged:

- **Model checkpoint**: Latest trained model (.pth)
- **Config file**: Training configuration (config.json)

## Advanced Usage

### Manual Tracking

You can use the MLflow tracker directly in Python:

```python
from vidchat.training.mlflow_tracker import create_rvc_tracker

# Create tracker
tracker = create_rvc_tracker("my_voice", epochs=300, batch_size=4)

# Start a run
with tracker.start_run():
    # Log parameters
    tracker.log_params({
        "learning_rate": 0.0001,
        "optimizer": "Adam",
    })

    # Training loop
    for epoch in range(10):
        loss = train_one_epoch()  # Your training code

        # Log metrics
        tracker.log_metric("loss", loss, step=epoch)

    # Log artifacts
    tracker.log_artifact("model.pth")
```

### Custom Tracking URI

By default, MLflow stores data in `.data/mlruns/`. To use a different location:

```python
from vidchat.training.mlflow_tracker import MLflowTracker

tracker = MLflowTracker(
    experiment_name="custom-experiment",
    tracking_uri="file:///path/to/mlruns",  # Custom location
)
```

## Troubleshooting

### "No MLflow experiments found"

If you see this message:
1. Make sure you've run training at least once
2. Check that `.data/mlruns/` directory exists
3. Verify training completed without errors

### MLflow UI not starting

If the UI won't start:
```bash
# Check if MLflow is installed
uv run python -c "import mlflow; print(mlflow.__version__)"

# Check if port is in use
lsof -i :5000

# Try a different port
uv run vidchat-cli mlflow-ui --port 8080
```

### Can't see recent runs

If new runs don't appear:
1. Refresh the browser
2. Click "Reload" in MLflow UI
3. Check the experiment filter (make sure "rvc-voice-training" is selected)

## Tips

1. **Name your experiments**: Use descriptive voice names for easy identification
2. **Compare systematically**: Change one parameter at a time to see its effect
3. **Track early**: Start tracking from the first experiment
4. **Download best models**: Use the UI to download your best checkpoint
5. **Clean old runs**: Periodically delete unsuccessful experiments

## References

- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [MLflow Tracking](https://mlflow.org/docs/latest/tracking.html)
- [MLflow UI](https://mlflow.org/docs/latest/tracking.html#tracking-ui)

## Next Steps

- [RVC Training Guide](RVC_QUICK_START.md) - How to train voice models
- [CLI Guide](CLI_GUIDE.md) - All CLI commands
- [Configuration](../config.example.yaml) - Training configuration options
