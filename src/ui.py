import sys
import select
import os
from typing import Any, Dict, Iterator, Optional, List, Tuple
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.console import Console
from pyfzf import FzfPrompt

try:
    import tty
    import termios
except ImportError:
    tty = None
    termios = None

class InputHandler:
    """Context manager to handle non-blocking input."""
    def __init__(self):
        self.fd = sys.stdin.fileno()
        # Only save settings if it's a TTY and termios is available
        if termios and tty and os.isatty(self.fd):
            self.old_settings = termios.tcgetattr(self.fd)
        else:
            self.old_settings = None

    def __enter__(self):
        if self.old_settings:
            tty.setcbreak(self.fd)
        return self

    def __exit__(self, type, value, traceback):
        if self.old_settings:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def get_key(self) -> Optional[str]:
        if self.old_settings:
            try:
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    return sys.stdin.read(1)
            except OSError:
                pass
        return None

def run_search(status_dict: Any, files: List[str], processed_files: set) -> None:
    """Launch FZF to search through file statuses."""
    fzf = FzfPrompt()

    lines = []

    # Snapshots active workers
    active_workers = {}
    try:
        active_workers = dict(status_dict)
    except:
        pass

    # Map file -> status
    file_status_map = {}
    for info in active_workers.values():
        if isinstance(info, dict):
            file_status_map[info.get("file")] = info.get("status", "Processing")

    for f in files:
        if f in processed_files:
            status = "Done"
        elif f in file_status_map:
            status = f"Processing ({file_status_map[f]})"
        else:
            status = "Pending"

        # Format: [Status] FilePath
        lines.append(f"[{status}] {f}")

    try:
        fzf.prompt(lines, "--header='File Status (Esc to exit)' --layout=reverse --border")
    except Exception:
        # FZF might fail if not installed or cancelled
        pass

def run_tui(status_dict: Any, result_iter: Iterator[Tuple[str, List[Any]]], writer: Any, output_path: str, files: List[str]) -> None:
    console = Console()
    total_files = len(files)
    processed_files = set()

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("{task.completed}/{task.total}"),
    )
    task_id = progress.add_task("Processing...", total=total_files)

    def generate_worker_table() -> Table:
        table = Table(title="Worker Status", expand=True)
        table.add_column("PID", style="cyan", width=8)
        table.add_column("Status", style="magenta", width=20)
        table.add_column("Current File", style="green")

        try:
            # Sort by PID for stability
            items = list(status_dict.items())
            for pid, info in sorted(items):
                table.add_row(str(pid), info.get("status", "Unknown"), info.get("file", ""))
        except Exception:
            pass
        return table

    def generate_layout() -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(Panel(progress, title="Overall Progress"), size=6),
            Layout(Panel(generate_worker_table(), title="Workers"), ratio=1),
            Layout(Panel("Press 's' to search active files", style="bold white on blue"), size=3)
        )
        return layout

    try:
        with InputHandler() as input_handler:
            # Only use screen=True if TTY
            use_screen = os.isatty(sys.stdin.fileno())

            with Live(generate_layout(), refresh_per_second=4, screen=use_screen) as live:
                for file_path, chunks in result_iter:
                    processed_files.add(file_path)

                    # Check for input
                    key = input_handler.get_key()
                    if key and key.lower() == 's':
                        live.stop()
                        if input_handler.old_settings:
                            termios.tcsetattr(input_handler.fd, termios.TCSADRAIN, input_handler.old_settings)
                        try:
                            run_search(status_dict, files, processed_files)
                        finally:
                            if input_handler.old_settings:
                                tty.setcbreak(input_handler.fd)
                            live.start()

                    if chunks:
                        writer.write(chunks, output_path)

                    progress.advance(task_id, advance=1)
                    live.update(generate_layout())

                progress.update(task_id, completed=total_files)

    except Exception as e:
        console.print(f"[red]Error in TUI: {e}[/red]")
        # Consume remaining items to avoid pool hang?
        # But we are exiting.
        raise
