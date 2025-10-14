"""
YouTube audio downloader using yt-dlp.
"""
import subprocess
import logging
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import DataPrepConfig


logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """
    Download audio from YouTube videos using yt-dlp.
    """

    def __init__(self, config: DataPrepConfig):
        """
        Initialize downloader.

        Args:
            config: Data preparation configuration
        """
        self.config = config
        self._verify_ytdlp()

    def _verify_ytdlp(self) -> bool:
        """Verify yt-dlp is installed."""
        try:
            result = subprocess.run(
                ["yt-dlp", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info(f"yt-dlp version: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            logger.error(
                "yt-dlp not found. Install with: pip install yt-dlp"
            )
            return False

        return False

    def download_audio(self, url: str, output_dir: Path) -> Optional[Path]:
        """
        Download audio from a single YouTube URL.

        Args:
            url: YouTube video URL
            output_dir: Directory to save audio files

        Returns:
            Path to downloaded audio file, or None if failed
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build yt-dlp command
        output_template = str(output_dir / "%(title)s.%(ext)s")

        cmd = [
            "yt-dlp",
            "-f", "bestaudio",
            "-x",  # Extract audio
            "--audio-format", self.config.audio_format,
            "--audio-quality", self.config.audio_quality,
            "-o", output_template,
            url
        ]

        if self.config.verbose:
            logger.info(f"Downloading audio from: {url}")
        else:
            cmd.append("--no-progress")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode == 0:
                # Find the downloaded file
                # yt-dlp prints the output filename
                for line in result.stdout.split('\n'):
                    if 'Destination:' in line or 'has already been downloaded' in line:
                        # Extract filename from output
                        continue

                # Alternative: find most recent file in output_dir
                files = list(output_dir.glob(f"*.{self.config.audio_format}"))
                if files:
                    latest = max(files, key=lambda p: p.stat().st_mtime)
                    logger.info(f"✓ Downloaded: {latest.name}")
                    return latest
                else:
                    logger.warning(f"Download succeeded but file not found for: {url}")
                    return None
            else:
                logger.error(f"✗ Download failed: {url}")
                logger.error(f"Error: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"✗ Download timeout: {url}")
            return None
        except Exception as e:
            logger.error(f"✗ Download error: {url} - {e}")
            return None

    def download_all(
        self,
        urls: Optional[List[str]] = None,
        parallel: Optional[int] = None
    ) -> List[Path]:
        """
        Download audio from multiple YouTube URLs.

        Args:
            urls: List of YouTube URLs (uses config.youtube_urls if None)
            parallel: Number of parallel downloads (uses config.parallel_downloads if None)

        Returns:
            List of successfully downloaded audio file paths
        """
        if urls is None:
            urls = self.config.youtube_urls

        if parallel is None:
            parallel = self.config.parallel_downloads

        if not urls:
            logger.warning("No URLs provided for download")
            return []

        output_dir = self.config.raw_audio_path
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading {len(urls)} videos with {parallel} parallel workers")

        downloaded_files = []

        if parallel == 1:
            # Sequential download
            for url in urls:
                file_path = self.download_audio(url, output_dir)
                if file_path:
                    downloaded_files.append(file_path)
        else:
            # Parallel download
            with ThreadPoolExecutor(max_workers=parallel) as executor:
                future_to_url = {
                    executor.submit(self.download_audio, url, output_dir): url
                    for url in urls
                }

                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        file_path = future.result()
                        if file_path:
                            downloaded_files.append(file_path)
                    except Exception as e:
                        logger.error(f"Error downloading {url}: {e}")

        logger.info(f"Successfully downloaded {len(downloaded_files)}/{len(urls)} files")

        return downloaded_files

    def download_from_file(self, file_path: str | Path) -> List[Path]:
        """
        Download audio from URLs listed in a text file.

        Args:
            file_path: Path to text file with one URL per line

        Returns:
            List of successfully downloaded audio file paths
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"URLs file not found: {file_path}")
            return []

        urls = []
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)

        logger.info(f"Loaded {len(urls)} URLs from {file_path}")

        return self.download_all(urls)
