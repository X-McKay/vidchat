#!/usr/bin/env python3
"""
Prepare voice data from YouTube URLs for voice cloning.

This script:
1. Downloads audio from YouTube URLs (from config.yaml)
2. Extracts and cleans audio
3. Segments audio into 10-second clips
4. Saves processed audio suitable for XTTS v2 reference

Note: With XTTS v2, you only need 6+ seconds of clean audio for voice cloning.
No training is required!
"""

import subprocess
import sys
import shutil
from pathlib import Path
from typing import Optional
import typer

app = typer.Typer(help="Prepare voice data from YouTube URLs for voice cloning")


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    required = ["yt-dlp", "ffmpeg"]
    missing = []

    for cmd in required:
        # Use shutil.which() for reliable detection
        if shutil.which(cmd) is None:
            missing.append(cmd)

    if missing:
        print(f"❌ Missing required dependencies: {', '.join(missing)}")
        print("\nInstall with:")
        for cmd in missing:
            if cmd == "yt-dlp":
                print("  pip install yt-dlp")
            elif cmd == "ffmpeg":
                print("  # Ubuntu/Debian: sudo apt install ffmpeg")
                print("  # macOS: brew install ffmpeg")
                print("  # Windows: Download from https://ffmpeg.org/")
        return False

    return True


def download_audio(url: str, output_path: Path) -> bool:
    """Download audio from YouTube URL."""
    print(f"Downloading: {url}")

    try:
        subprocess.run(
            [
                "yt-dlp",
                "-x",  # Extract audio
                "--audio-format",
                "wav",
                "--audio-quality",
                "0",  # Best quality
                "-o",
                str(output_path / "%(id)s.%(ext)s"),
                url,
            ],
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error downloading {url}: {e}")
        return False


def process_audio(
    input_file: Path, output_dir: Path, segment_length: int = 10
) -> list[Path]:
    """Process audio: normalize, remove silence, and segment."""
    print(f"Processing: {input_file.name}")

    # Create temp file for normalized audio
    temp_normalized = output_dir / f"temp_normalized_{input_file.stem}.wav"

    # Step 1: Normalize and convert to mono 44.1kHz
    print("  - Normalizing audio...")
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(input_file),
                "-ar",
                "44100",  # 44.1kHz sample rate
                "-ac",
                "1",  # Mono
                "-filter:a",
                "loudnorm",  # Normalize loudness
                "-y",  # Overwrite
                str(temp_normalized),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout normalizing audio (>5 minutes)")
        return []
    except subprocess.CalledProcessError as e:
        print(f"❌ Error normalizing audio: {e}")
        if e.stderr:
            print(f"   FFmpeg error: {e.stderr[-500:]}")  # Show last 500 chars
        return []

    # Step 2: Remove silence from beginning/end only
    temp_trimmed = output_dir / f"temp_trimmed_{input_file.stem}.wav"
    print("  - Removing silence from start/end...")
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(temp_normalized),
                "-af",
                "silenceremove=start_periods=1:start_duration=0.5:start_threshold=-50dB:stop_periods=-1:stop_duration=0.5:stop_threshold=-50dB",  # Remove silence from beginning and end only
                "-y",
                str(temp_trimmed),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout removing silence (>5 minutes)")
        temp_normalized.unlink(missing_ok=True)
        return []
    except subprocess.CalledProcessError as e:
        print(f"❌ Error removing silence: {e}")
        if e.stderr:
            print(f"   FFmpeg error: {e.stderr[-500:]}")
        temp_normalized.unlink(missing_ok=True)
        return []

    # Clean up temp file
    temp_normalized.unlink(missing_ok=True)

    # Step 3: Segment into fixed-length clips
    print(f"  - Segmenting into {segment_length}s clips...")
    segments = []

    try:
        # Get duration
        result = subprocess.run(
            [
                "ffprobe",
                "-i",
                str(temp_trimmed),
                "-show_entries",
                "format=duration",
                "-v",
                "quiet",
                "-of",
                "csv=p=0",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        duration = float(result.stdout.strip())

        # Create segments
        num_segments = int(duration / segment_length)
        for i in range(num_segments):
            segment_file = output_dir / f"segment_{i:04d}.wav"
            start_time = i * segment_length

            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    str(temp_trimmed),
                    "-ss",
                    str(start_time),
                    "-t",
                    str(segment_length),
                    "-acodec",
                    "pcm_s16le",  # 16-bit PCM
                    "-y",
                    str(segment_file),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            segments.append(segment_file)

        print(f"  ✓ Created {len(segments)} segments")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error segmenting audio: {e}")
    finally:
        temp_trimmed.unlink(missing_ok=True)

    return segments


@app.command()
def prepare(
    voice_name: str = typer.Option(
        None, "--name", "-n", help="Voice name (from config if not specified)"
    ),
    urls: Optional[list[str]] = typer.Option(
        None, "--url", "-u", help="YouTube URLs (from config if not specified)"
    ),
    segment_length: int = typer.Option(
        10, "--segment-length", "-s", help="Segment length in seconds"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory (auto-detected if not specified)"
    ),
):
    """Prepare voice data from YouTube URLs for voice cloning."""

    # Check dependencies first
    if not check_dependencies():
        raise typer.Exit(1)

    # Load config if needed
    if voice_name is None or urls is None:
        try:
            from vidchat.utils.config_loader import load_config

            config = load_config()
            if voice_name is None:
                voice_name = config.voice_training.voice_name
            if urls is None:
                urls = config.voice_training.training_urls

            if not urls:
                print("❌ No URLs provided and none found in config.yaml")
                raise typer.Exit(1)

        except Exception as e:
            print(f"❌ Error loading config: {e}")
            print("\nPlease provide --name and --url options, or create config.yaml")
            raise typer.Exit(1)

    # Determine output directory
    if output_dir is None:
        # Find project root by looking for pyproject.toml
        current = Path.cwd()
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                project_root = current
                break
            current = current.parent
        else:
            project_root = Path.cwd()

        # Use .data/voice_data/<voice_name> in the repository
        output_dir = project_root / ".data" / "voice_data" / voice_name
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("VidChat Voice Data Preparation")
    print("=" * 80)
    print(f"\nVoice name: {voice_name}")
    print(f"URLs: {len(urls)}")
    print(f"Output directory: {output_dir}")
    print(f"Segment length: {segment_length}s")
    print()

    # Create temp download directory
    download_dir = output_dir / "downloads"
    download_dir.mkdir(exist_ok=True)

    # Download all URLs
    downloaded_files = []
    existing_files = set()  # Track already-seen files
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Downloading from YouTube...")
        if download_audio(url, download_dir):
            # Find newly downloaded file
            wav_files = list(download_dir.glob("*.wav"))
            for f in wav_files:
                if f not in existing_files:
                    downloaded_files.append(f)
                    existing_files.add(f)

    if not downloaded_files:
        print("\n❌ No audio files were downloaded")
        raise typer.Exit(1)

    print(f"\n✓ Downloaded {len(downloaded_files)} audio files")
    print()

    # Process each downloaded file
    all_segments = []
    for audio_file in downloaded_files:
        segments = process_audio(audio_file, output_dir, segment_length)
        all_segments.extend(segments)
        # Clean up downloaded file (if processing succeeded)
        audio_file.unlink(missing_ok=True)

    # Clean up download directory (if empty)
    try:
        download_dir.rmdir()
    except OSError:
        # Directory not empty or doesn't exist - that's okay
        pass

    # Summary
    print()
    print("=" * 80)
    print("✓ Voice data preparation complete!")
    print("=" * 80)
    print(f"\nGenerated {len(all_segments)} audio segments")
    print(f"Location: {output_dir}")
    print()

    if all_segments:
        print("Sample segments:")
        for segment in all_segments[:5]:
            size = segment.stat().st_size / 1024
            print(f"  {segment.name} ({size:.1f}KB)")
        if len(all_segments) > 5:
            print(f"  ... and {len(all_segments) - 5} more")

    if all_segments:
        print()
        print("Next steps:")
        print("1. Listen to the segments to verify quality")
        print("2. Use any segment (6+ seconds) as reference audio for XTTS v2")
        print("3. Configure VidChat:")
        print()
        print("   # config.yaml")
        print("   tts:")
        print('     provider: "xtts"')
        print("     xtts:")
        print(f'       reference_audio: "{all_segments[0]}"')
        print('       language: "en"')
        print()
        print("4. Test voice cloning:")
        print("   uv run python demo_voice_cloning.py")
    else:
        print()
        print("⚠️  No segments were created - all audio processing failed")
        print()
        print("Common causes:")
        print("  - FFmpeg processing errors (exit codes 222/254)")
        print("  - Corrupted or incompatible audio files")
        print("  - Insufficient system resources")
        print()
        print("Troubleshooting:")
        print("  1. Check downloaded files:")
        print(f"     ls -lh {output_dir / 'downloads'}/")
        print("  2. Test one file manually:")
        print(f"     ffmpeg -i {output_dir / 'downloads'}/ST6HJQutdV8.wav -ar 44100 -ac 1 test.wav")
        print("  3. Check system resources (disk space, memory)")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
