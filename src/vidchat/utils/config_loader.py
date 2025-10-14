"""Configuration loader for VidChat.

Loads configuration from config.yaml file with fallback defaults.
"""

import yaml
from pathlib import Path
from typing import Any, Dict
from dataclasses import dataclass


@dataclass
class PathConfig:
    """Path configuration."""
    data_dir: Path
    models_dir: Path
    output_dir: Path
    external_dir: Path
    sadtalker_dir: Path
    rvc_dir: Path
    voice_data: Path
    training_data: Path
    downloads: Path
    logs: Path


@dataclass
class VoiceTrainingConfig:
    """Voice training configuration."""
    voice_name: str
    training_urls: list[str]
    epochs: int
    batch_size: int
    sample_rate: int
    segment_length: int
    min_segment_length: int
    silence_threshold: int


@dataclass
class AppSettings:
    """Application settings."""
    window_name: str
    fps: int
    width: int
    height: int


@dataclass
class XTTSConfig:
    """XTTS voice cloning configuration."""
    reference_audio: Path
    language: str = "en"


@dataclass
class TTSConfig:
    """TTS configuration."""
    provider: str  # "piper", "xtts", or "hybrid"
    piper_model: str
    xtts: XTTSConfig | None = None


@dataclass
class VidChatConfig:
    """Main VidChat configuration."""
    voice_training: VoiceTrainingConfig
    paths: PathConfig
    app: AppSettings
    tts: TTSConfig
    raw_config: Dict[str, Any]


def get_project_root() -> Path:
    """Get the project root directory."""
    # Start from this file and go up to find pyproject.toml
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    # Fallback to current working directory
    return Path.cwd()


def load_config(config_path: str | Path | None = None) -> VidChatConfig:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, looks for config.yaml in project root.

    Returns:
        VidChatConfig with loaded settings.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        yaml.YAMLError: If config file is invalid.
    """
    if config_path is None:
        project_root = get_project_root()
        config_path = project_root / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            f"Create config.yaml in project root or specify path."
        )

    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)

    # Get project root for resolving relative paths
    project_root = get_project_root()

    # Parse paths
    paths_dict = config_dict.get('paths', {})
    paths = PathConfig(
        data_dir=project_root / paths_dict.get('data_dir', '.data'),
        models_dir=project_root / paths_dict.get('models_dir', 'models'),
        output_dir=project_root / paths_dict.get('output_dir', 'output'),
        external_dir=project_root / paths_dict.get('external_dir', 'external'),
        sadtalker_dir=project_root / paths_dict.get('sadtalker_dir', 'external/SadTalker'),
        rvc_dir=project_root / paths_dict.get('rvc_dir', 'external/RVC'),
        voice_data=project_root / paths_dict.get('data_dir', '.data') / paths_dict.get('voice_data', 'voice_data'),
        training_data=project_root / paths_dict.get('data_dir', '.data') / paths_dict.get('training_data', 'training'),
        downloads=project_root / paths_dict.get('data_dir', '.data') / paths_dict.get('downloads', 'downloads'),
        logs=project_root / paths_dict.get('data_dir', '.data') / paths_dict.get('logs', 'logs'),
    )

    # Parse voice training config
    vt_dict = config_dict.get('voice_training', {})
    voice_training = VoiceTrainingConfig(
        voice_name=vt_dict.get('voice_name', 'my_voice'),
        training_urls=vt_dict.get('training_urls', []),
        epochs=vt_dict.get('epochs', 300),
        batch_size=vt_dict.get('batch_size', 4),
        sample_rate=vt_dict.get('sample_rate', 40000),
        segment_length=vt_dict.get('segment_length', 10),
        min_segment_length=vt_dict.get('min_segment_length', 3),
        silence_threshold=vt_dict.get('silence_threshold', -40),
    )

    # Parse app settings
    app_dict = config_dict.get('app', {})
    app = AppSettings(
        window_name=app_dict.get('window_name', 'VidChat'),
        fps=app_dict.get('fps', 30),
        width=app_dict.get('width', 800),
        height=app_dict.get('height', 600),
    )

    # Parse TTS settings
    tts_dict = config_dict.get('tts', {})
    xtts_config = None
    if 'xtts' in tts_dict:
        xtts_dict = tts_dict['xtts']
        ref_audio_path = Path(xtts_dict.get('reference_audio', '')).expanduser()
        # Make relative to project root if not absolute
        if not ref_audio_path.is_absolute():
            ref_audio_path = project_root / ref_audio_path
        xtts_config = XTTSConfig(
            reference_audio=ref_audio_path,
            language=xtts_dict.get('language', 'en'),
        )

    tts = TTSConfig(
        provider=tts_dict.get('provider', 'piper'),
        piper_model=tts_dict.get('piper_model', 'en_US-lessac-medium'),
        xtts=xtts_config,
    )

    return VidChatConfig(
        voice_training=voice_training,
        paths=paths,
        app=app,
        tts=tts,
        raw_config=config_dict,
    )


def get_youtube_urls() -> list[str]:
    """Get YouTube URLs from config for voice training.

    Returns:
        List of YouTube URLs from config.yaml
    """
    config = load_config()
    return config.voice_training.training_urls


# Example usage
if __name__ == "__main__":
    config = load_config()
    print(f"Voice name: {config.voice_training.voice_name}")
    print(f"Training URLs: {config.voice_training.training_urls}")
    print(f"Data directory: {config.paths.data_dir}")
    print(f"Models directory: {config.paths.models_dir}")
