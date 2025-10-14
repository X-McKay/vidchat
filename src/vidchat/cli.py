#!/usr/bin/env python3
"""
VidChat CLI - Comprehensive command-line interface for managing VidChat services.

Usage:
    vidchat-cli status              # Check status of all services
    vidchat-cli start web           # Start web server
    vidchat-cli start ollama        # Start Ollama service
    vidchat-cli start all           # Start all services
    vidchat-cli stop all            # Stop all services
    vidchat-cli install             # Install all dependencies
    vidchat-cli models              # Download required models
"""

import os
import sys
import time
import signal
import subprocess
import shutil
import datetime
from pathlib import Path
from typing import Optional, List
import psutil

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

app = typer.Typer(
    name="vidchat-cli",
    help="VidChat Service Management CLI",
    add_completion=True,
)

console = Console()

# Global process tracking
processes = {}


def find_project_root() -> Path:
    """Find the VidChat project root directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()


PROJECT_ROOT = find_project_root()
FRONTEND_DIR = PROJECT_ROOT / "src" / "vidchat" / "web" / "frontend"
MODELS_DIR = PROJECT_ROOT / "models"


def is_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            return True
    return False


def find_process_by_port(port: int) -> Optional[psutil.Process]:
    """Find process using a specific port."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            for conn in proc.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def find_process_by_name(name: str) -> List[psutil.Process]:
    """Find processes by name pattern."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.cmdline())
            if name.lower() in cmdline.lower() or name.lower() in proc.name().lower():
                processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes


def check_ollama_status() -> dict:
    """Check if Ollama is running."""
    port_in_use = is_port_in_use(11434)
    process = find_process_by_port(11434)

    # Also check if ollama command exists
    ollama_exists = shutil.which('ollama') is not None

    # Check if model is available
    model_available = False
    if ollama_exists and port_in_use:
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            model_available = 'llama3.2' in result.stdout
        except:
            pass

    return {
        'running': port_in_use,
        'process': process,
        'installed': ollama_exists,
        'model_available': model_available,
        'port': 11434
    }


def check_web_server_status() -> dict:
    """Check if web server is running."""
    port_in_use = is_port_in_use(8000)
    process = find_process_by_port(8000)

    # Check if frontend is built
    frontend_built = (FRONTEND_DIR / "dist" / "index.html").exists() if FRONTEND_DIR.exists() else False

    return {
        'running': port_in_use,
        'process': process,
        'frontend_built': frontend_built,
        'port': 8000
    }


def check_dependencies() -> dict:
    """Check if Python and Node dependencies are installed."""
    # Check Python venv
    venv_exists = (PROJECT_ROOT / ".venv").exists()

    # Check if key Python packages are importable
    python_deps_ok = False
    if venv_exists:
        try:
            result = subprocess.run(
                ['uv', 'run', 'python', '-c', 'import vidchat, typer, fastapi'],
                cwd=PROJECT_ROOT,
                capture_output=True,
                timeout=10
            )
            python_deps_ok = result.returncode == 0
        except:
            pass

    # Check Node dependencies
    node_deps_ok = (FRONTEND_DIR / "node_modules").exists() if FRONTEND_DIR.exists() else False

    # Check if models exist
    piper_model_exists = (MODELS_DIR / "en_US-lessac-medium.onnx").exists()

    return {
        'venv_exists': venv_exists,
        'python_deps_ok': python_deps_ok,
        'node_deps_ok': node_deps_ok,
        'piper_model_exists': piper_model_exists
    }


@app.command()
def status():
    """Check the status of all VidChat services."""
    console.print("\n[bold cyan]VidChat Service Status[/bold cyan]\n")

    # Check Ollama
    ollama_status = check_ollama_status()
    web_status = check_web_server_status()
    deps_status = check_dependencies()

    # Create status table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Service", style="cyan", width=20)
    table.add_column("Status", width=15)
    table.add_column("Details", width=50)

    # Ollama status
    if ollama_status['running']:
        status_text = "[green]✓ Running[/green]"
        details = f"Port {ollama_status['port']}, PID: {ollama_status['process'].pid if ollama_status['process'] else 'N/A'}"
        if ollama_status['model_available']:
            details += " | llama3.2 available ✓"
        else:
            details += " | [yellow]llama3.2 not found[/yellow]"
    elif ollama_status['installed']:
        status_text = "[yellow]○ Stopped[/yellow]"
        details = "Ollama installed but not running"
    else:
        status_text = "[red]✗ Not installed[/red]"
        details = "Install from https://ollama.com"

    table.add_row("Ollama", status_text, details)

    # Web server status
    if web_status['running']:
        status_text = "[green]✓ Running[/green]"
        details = f"Port {web_status['port']}, PID: {web_status['process'].pid if web_status['process'] else 'N/A'}"
        if web_status['frontend_built']:
            details += " | Frontend built ✓"
        else:
            details += " | [yellow]Frontend not built[/yellow]"
    else:
        status_text = "[yellow]○ Stopped[/yellow]"
        if web_status['frontend_built']:
            details = "Frontend ready, server not running"
        else:
            details = "[yellow]Frontend not built[/yellow] - run 'vidchat-cli build'"

    table.add_row("Web Server", status_text, details)

    # Dependencies status
    if deps_status['python_deps_ok']:
        status_text = "[green]✓ Installed[/green]"
        details = "Python dependencies OK"
    elif deps_status['venv_exists']:
        status_text = "[yellow]○ Incomplete[/yellow]"
        details = "Virtual env exists but packages missing"
    else:
        status_text = "[red]✗ Not installed[/red]"
        details = "Run 'vidchat-cli install'"

    table.add_row("Python Deps", status_text, details)

    if deps_status['node_deps_ok']:
        status_text = "[green]✓ Installed[/green]"
        details = "Node dependencies OK"
    else:
        status_text = "[red]✗ Not installed[/red]"
        details = "Run 'vidchat-cli install'"

    table.add_row("Node Deps", status_text, details)

    # Models status
    if deps_status['piper_model_exists']:
        status_text = "[green]✓ Available[/green]"
        details = "Piper TTS model downloaded"
    else:
        status_text = "[red]✗ Missing[/red]"
        details = "Run 'vidchat-cli models'"

    table.add_row("TTS Models", status_text, details)

    console.print(table)
    console.print()


@app.command()
def install(
    all_extras: bool = typer.Option(False, "--all", help="Install all optional dependencies"),
    web: bool = typer.Option(True, "--web/--no-web", help="Install web dependencies"),
    voice_prep: bool = typer.Option(False, "--voice-prep", help="Install voice prep dependencies")
):
    """Install all required dependencies."""
    console.print("\n[bold cyan]Installing VidChat Dependencies[/bold cyan]\n")

    # Build extras string
    extras = []
    if all_extras:
        extras.append("--all-extras")
    else:
        if web:
            extras.append("--extra")
            extras.append("web")
        if voice_prep:
            extras.append("--extra")
            extras.append("voice-prep")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Install Python dependencies
        task = progress.add_task("Installing Python dependencies...", total=None)

        cmd = ["uv", "sync"] + extras
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)

        if result.returncode == 0:
            progress.update(task, description="[green]✓ Python dependencies installed[/green]")
        else:
            progress.update(task, description="[red]✗ Failed to install Python dependencies[/red]")
            console.print(f"\n[red]Error:[/red] {result.stderr}")
            raise typer.Exit(1)

        progress.stop()

        # Install Node dependencies if frontend exists
        if FRONTEND_DIR.exists():
            task = progress.add_task("Installing Node dependencies...", total=None)

            result = subprocess.run(
                ["npm", "install", "--legacy-peer-deps"],
                cwd=FRONTEND_DIR,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                progress.update(task, description="[green]✓ Node dependencies installed[/green]")
            else:
                progress.update(task, description="[red]✗ Failed to install Node dependencies[/red]")
                console.print(f"\n[red]Error:[/red] {result.stderr}")
                raise typer.Exit(1)

    console.print("\n[green]✓ All dependencies installed successfully![/green]\n")


@app.command()
def models():
    """Download required AI and TTS models."""
    console.print("\n[bold cyan]Downloading Models[/bold cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Download Ollama model
        task1 = progress.add_task("Downloading llama3.2 model...", total=None)

        result = subprocess.run(
            ["ollama", "pull", "llama3.2"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            progress.update(task1, description="[green]✓ llama3.2 downloaded[/green]")
        else:
            progress.update(task1, description="[yellow]⚠ Failed to download llama3.2[/yellow]")
            console.print(f"[yellow]Make sure Ollama is installed and running[/yellow]")

        # Download Piper model
        task2 = progress.add_task("Downloading Piper TTS model...", total=None)

        MODELS_DIR.mkdir(exist_ok=True)

        model_url = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
        config_url = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"

        model_file = MODELS_DIR / "en_US-lessac-medium.onnx"
        config_file = MODELS_DIR / "en_US-lessac-medium.onnx.json"

        # Download model if not exists
        if not model_file.exists():
            result = subprocess.run(
                ["wget", "-q", "-O", str(model_file), model_url],
                capture_output=True
            )
            if result.returncode != 0:
                progress.update(task2, description="[red]✗ Failed to download Piper model[/red]")
                raise typer.Exit(1)

        # Download config if not exists
        if not config_file.exists():
            result = subprocess.run(
                ["wget", "-q", "-O", str(config_file), config_url],
                capture_output=True
            )

        progress.update(task2, description="[green]✓ Piper TTS model downloaded[/green]")

    console.print("\n[green]✓ All models downloaded successfully![/green]\n")


@app.command()
def build():
    """Build the frontend."""
    console.print("\n[bold cyan]Building Frontend[/bold cyan]\n")

    if not FRONTEND_DIR.exists():
        console.print("[red]Error: Frontend directory not found[/red]")
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Building React frontend...", total=None)

        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=FRONTEND_DIR,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            progress.update(task, description="[green]✓ Frontend built successfully[/green]")
        else:
            progress.update(task, description="[red]✗ Frontend build failed[/red]")
            console.print(f"\n[red]Error:[/red]\n{result.stderr}")
            raise typer.Exit(1)

    console.print("\n[green]✓ Frontend ready![/green]\n")


@app.command()
def start(
    service: str = typer.Argument("web", help="Service to start: web, ollama, all (default: web)"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to (web server only)"),
    port: int = typer.Option(8000, "--port", help="Port to bind to (web server only)"),
    background: bool = typer.Option(True, "--background/--foreground", "-d/-f", help="Run in background (default: True)")
):
    """Start VidChat services (defaults to starting web server in background)."""
    service = service.lower()

    if service == "ollama":
        start_ollama(background)
    elif service == "web":
        start_web(host, port, background)
    elif service == "all":
        start_ollama(background=True)
        time.sleep(2)  # Give Ollama time to start
        start_web(host, port, background)
    else:
        console.print(f"[red]Unknown service: {service}[/red]")
        console.print("Available services: web, ollama, all")
        raise typer.Exit(1)


def start_ollama(background: bool = False):
    """Start Ollama service."""
    status = check_ollama_status()

    if status['running']:
        console.print("[yellow]Ollama is already running[/yellow]")
        return

    if not status['installed']:
        console.print("[red]Error: Ollama is not installed[/red]")
        console.print("Install from: https://ollama.com")
        raise typer.Exit(1)

    console.print("[cyan]Starting Ollama...[/cyan]")

    if background:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        time.sleep(2)

        if check_ollama_status()['running']:
            console.print("[green]✓ Ollama started in background[/green]")
        else:
            console.print("[red]✗ Failed to start Ollama[/red]")
            raise typer.Exit(1)
    else:
        console.print("Press Ctrl+C to stop")
        try:
            subprocess.run(["ollama", "serve"])
        except KeyboardInterrupt:
            console.print("\n[yellow]Ollama stopped[/yellow]")


def start_web(host: str = "127.0.0.1", port: int = 8000, background: bool = False):
    """Start web server."""
    status = check_web_server_status()

    if status['running']:
        console.print("[yellow]Web server is already running[/yellow]")
        return

    if not status['frontend_built']:
        console.print("[yellow]Frontend not built. Building now...[/yellow]")
        build()

    # Check if Ollama is running
    ollama_status = check_ollama_status()
    if not ollama_status['running']:
        console.print("[yellow]⚠ Warning: Ollama is not running[/yellow]")
        console.print("Start Ollama with: vidchat-cli start ollama")

    console.print(f"[cyan]Starting web server on {host}:{port}...[/cyan]")
    console.print(f"[cyan]Access at: http://{host}:{port}[/cyan]")

    if background:
        subprocess.Popen(
            ["uv", "run", "uvicorn", "vidchat.web.server:app",
             "--host", host, "--port", str(port)],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        time.sleep(3)

        if check_web_server_status()['running']:
            console.print(f"[green]✓ Web server started in background[/green]")
            console.print(f"[green]Access at: http://{host}:{port}[/green]")
        else:
            console.print("[red]✗ Failed to start web server[/red]")
            raise typer.Exit(1)
    else:
        console.print("Press Ctrl+C to stop")
        try:
            subprocess.run(
                ["uv", "run", "uvicorn", "vidchat.web.server:app",
                 "--host", host, "--port", str(port)],
                cwd=PROJECT_ROOT
            )
        except KeyboardInterrupt:
            console.print("\n[yellow]Web server stopped[/yellow]")


@app.command()
def stop(
    service: str = typer.Argument("all", help="Service to stop: web, ollama, all (default: all)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force kill processes")
):
    """Stop VidChat services (defaults to stopping all services)."""
    service = service.lower()

    if service == "web":
        stop_web(force)
    elif service == "ollama":
        stop_ollama(force)
    elif service == "all":
        stop_web(force)
        stop_ollama(force)
    else:
        console.print(f"[red]Unknown service: {service}[/red]")
        raise typer.Exit(1)


def stop_web(force: bool = False):
    """Stop web server."""
    process = find_process_by_port(8000)

    if not process:
        console.print("[yellow]Web server is not running[/yellow]")
        return

    console.print(f"[cyan]Stopping web server (PID: {process.pid})...[/cyan]")

    try:
        if force:
            process.kill()
        else:
            process.terminate()
            process.wait(timeout=10)

        console.print("[green]✓ Web server stopped[/green]")
    except psutil.TimeoutExpired:
        console.print("[yellow]Process didn't stop gracefully, killing...[/yellow]")
        process.kill()
        console.print("[green]✓ Web server killed[/green]")
    except psutil.NoSuchProcess:
        console.print("[yellow]Process already stopped[/yellow]")


def stop_ollama(force: bool = False):
    """Stop Ollama service."""
    process = find_process_by_port(11434)

    if not process:
        console.print("[yellow]Ollama is not running[/yellow]")
        return

    console.print(f"[cyan]Stopping Ollama (PID: {process.pid})...[/cyan]")

    try:
        if force:
            process.kill()
        else:
            process.terminate()
            process.wait(timeout=10)

        console.print("[green]✓ Ollama stopped[/green]")
    except psutil.TimeoutExpired:
        console.print("[yellow]Process didn't stop gracefully, killing...[/yellow]")
        process.kill()
        console.print("[green]✓ Ollama killed[/green]")
    except psutil.NoSuchProcess:
        console.print("[yellow]Process already stopped[/yellow]")


@app.command()
def logs(
    service: str = typer.Argument("web", help="Service to show logs for: web, ollama"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output")
):
    """Show service logs (placeholder - implement with proper logging)."""
    console.print(f"[yellow]Log viewing not yet implemented for {service}[/yellow]")
    console.print("Check system logs or run services in foreground for now")


@app.command()
def clean():
    """Clean build artifacts and cache."""
    console.print("\n[bold cyan]Cleaning Build Artifacts[/bold cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Cleaning...", total=None)

        # Clean frontend dist
        if (FRONTEND_DIR / "dist").exists():
            shutil.rmtree(FRONTEND_DIR / "dist")

        # Clean Python cache
        for path in PROJECT_ROOT.rglob("__pycache__"):
            shutil.rmtree(path, ignore_errors=True)

        for path in PROJECT_ROOT.rglob("*.pyc"):
            path.unlink(missing_ok=True)

        progress.update(task, description="[green]✓ Cleaned[/green]")

    console.print("\n[green]✓ Build artifacts cleaned![/green]\n")


@app.command()
def train_rvc(
    experiment: str = typer.Argument("my_voice", help="Experiment name"),
    epochs: int = typer.Option(200, "--epochs", "-e", help="Total training epochs"),
    batch_size: int = typer.Option(4, "--batch-size", "-b", help="Batch size"),
    save_freq: int = typer.Option(10, "--save-freq", "-s", help="Save checkpoint every N epochs"),
    gpu: bool = typer.Option(False, "--gpu", "-g", help="Use GPU (if compatible)"),
    background: bool = typer.Option(True, "--background", "-d", help="Run in background")
):
    """Train an RVC voice model."""
    rvc_dir = Path.home() / "RVC"
    exp_dir = rvc_dir / "logs" / experiment

    if not rvc_dir.exists():
        console.print("[red]Error: RVC not found at ~/RVC[/red]")
        console.print("Clone RVC with: git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI ~/RVC")
        raise typer.Exit(1)

    if not exp_dir.exists():
        console.print(f"[red]Error: Experiment '{experiment}' not found at {exp_dir}[/red]")
        console.print("Make sure you've prepared the dataset first.")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]Starting RVC Training[/bold cyan]\n")
    console.print(f"Experiment: {experiment}")
    console.print(f"Epochs: {epochs}")
    console.print(f"Batch size: {batch_size}")
    console.print(f"Mode: {'GPU' if gpu else 'CPU'}")
    console.print(f"Save frequency: Every {save_freq} epochs")

    device = "0" if gpu else "cpu"
    python_cmd = str(Path.home() / ".local/share/mise/installs/python/3.10.19/bin/python3")

    cmd = [
        python_cmd,
        str(rvc_dir / "infer/modules/train/train.py"),
        "-e", experiment,
        "-sr", "40k",
        "-f0", "1",
        "-bs", str(batch_size),
        "-g", device,
        "-te", str(epochs),
        "-se", str(save_freq),
        "-pg", str(rvc_dir / "assets/pretrained_v2/f0G40k.pth"),
        "-pd", str(rvc_dir / "assets/pretrained_v2/f0D40k.pth"),
        "-l", "1",
        "-c", "0",
        "-sw", "1",
        "-v", "v2"
    ]

    env = os.environ.copy()
    if not gpu:
        env["CUDA_VISIBLE_DEVICES"] = ""

    log_file = exp_dir / "train.log"

    if background:
        console.print(f"\n[cyan]Starting training in background...[/cyan]")

        with open(log_file, "w") as f:
            process = subprocess.Popen(
                cmd,
                cwd=rvc_dir,
                stdout=f,
                stderr=subprocess.STDOUT,
                env=env,
                start_new_session=True
            )

        time.sleep(2)

        # Check if process is still running
        if process.poll() is None:
            console.print(f"[green]✓ Training started (PID: {process.pid})[/green]")
            console.print(f"\n[yellow]Monitor progress with:[/yellow]")
            console.print(f"  vidchat-cli rvc-status {experiment}")
            console.print(f"\n[yellow]Or tail the log:[/yellow]")
            console.print(f"  tail -f {log_file}")
            console.print(f"\n[yellow]Check checkpoints:[/yellow]")
            console.print(f"  ls -lh {exp_dir}/*.pth")
        else:
            console.print(f"[red]✗ Training failed to start[/red]")
            console.print(f"Check log: {log_file}")
            raise typer.Exit(1)
    else:
        console.print(f"\n[cyan]Starting training (foreground)...[/cyan]")
        console.print("[yellow]Press Ctrl+C to stop[/yellow]\n")

        try:
            subprocess.run(cmd, cwd=rvc_dir, env=env)
        except KeyboardInterrupt:
            console.print("\n[yellow]Training interrupted[/yellow]")


@app.command()
def rvc_status(
    experiment: str = typer.Argument("my_voice", help="Experiment name"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output")
):
    """Check RVC training status and progress."""
    rvc_dir = Path.home() / "RVC"
    exp_dir = rvc_dir / "logs" / experiment
    log_file = exp_dir / "train.log"

    if not exp_dir.exists():
        console.print(f"[red]Error: Experiment '{experiment}' not found[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]RVC Training Status: {experiment}[/bold cyan]\n")

    # Check for checkpoints
    checkpoints = sorted(exp_dir.glob("G_*.pth"))
    if checkpoints:
        latest = checkpoints[-1]
        epoch = latest.stem.split("_")[1]
        console.print(f"[green]Latest checkpoint: {latest.name} (Epoch {epoch})[/green]")
        console.print(f"Total checkpoints: {len(checkpoints)}")

        # Show file sizes
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Checkpoint", style="cyan")
        table.add_column("Size", style="green")
        table.add_column("Modified", style="yellow")

        for cp in checkpoints[-5:]:  # Show last 5
            size = cp.stat().st_size / (1024 * 1024)  # MB
            mtime = datetime.datetime.fromtimestamp(cp.stat().st_mtime)
            table.add_row(
                cp.name,
                f"{size:.1f} MB",
                mtime.strftime("%Y-%m-%d %H:%M:%S")
            )

        console.print(table)
    else:
        console.print("[yellow]No checkpoints found yet[/yellow]")

    console.print()

    # Check if training is running
    training_running = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.cmdline())
            if 'train.py' in cmdline and experiment in cmdline:
                training_running = True
                console.print(f"[green]✓ Training is running (PID: {proc.pid})[/green]")
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not training_running:
        console.print("[yellow]○ Training is not running[/yellow]")

    # Show log tail
    if log_file.exists():
        console.print(f"\n[cyan]Recent log output:[/cyan]\n")

        if follow:
            console.print("[yellow]Following log (Ctrl+C to stop)...[/yellow]\n")
            try:
                subprocess.run(["tail", "-f", str(log_file)])
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopped following log[/yellow]")
        else:
            result = subprocess.run(
                ["tail", "-20", str(log_file)],
                capture_output=True,
                text=True
            )
            console.print(result.stdout)

            console.print(f"\n[yellow]To follow log in real-time:[/yellow]")
            console.print(f"  vidchat-cli rvc-status {experiment} --follow")
    else:
        console.print("[yellow]No log file found yet[/yellow]")

    console.print()


@app.command()
def mlflow_ui(
    port: int = typer.Option(5000, "--port", "-p", help="Port for MLflow UI"),
    background: bool = typer.Option(False, "--background", "-d", help="Run in background"),
):
    """Start MLflow UI to visualize training experiments."""
    console.print("[bold cyan]MLflow Experiment Tracking UI[/bold cyan]\n")

    try:
        from vidchat.utils.config_loader import get_project_root
        project_root = get_project_root()
        mlruns_dir = project_root / ".data" / "mlruns"
    except:
        mlruns_dir = Path.cwd() / ".data" / "mlruns"

    if not mlruns_dir.exists():
        console.print("[yellow]⚠ No MLflow experiments found[/yellow]")
        console.print(f"   Expected location: {mlruns_dir}")
        console.print("\n[dim]Run training with MLflow tracking first:[/dim]")
        console.print("  uv run vidchat-cli train-rvc <voice_name>")
        return

    console.print(f"📊 MLflow tracking directory: {mlruns_dir}")
    console.print(f"🌐 Starting UI on port {port}...\n")

    cmd = [
        "mlflow",
        "ui",
        "--backend-store-uri",
        mlruns_dir.as_uri(),
        "--port",
        str(port),
    ]

    if background:
        console.print(f"✓ MLflow UI starting in background")
        console.print(f"  Access at: [link]http://localhost:{port}[/link]")
        console.print(f"\n[dim]To stop: pkill -f 'mlflow ui'[/dim]\n")
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    else:
        console.print(f"✓ MLflow UI running")
        console.print(f"  Access at: [link]http://localhost:{port}[/link]")
        console.print(f"\n[dim]Press Ctrl+C to stop[/dim]\n")
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            console.print("\n\n[yellow]MLflow UI stopped[/yellow]")


if __name__ == "__main__":
    app()
