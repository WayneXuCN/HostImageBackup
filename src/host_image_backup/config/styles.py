from pathlib import Path
from typing import Any

from rich import print as rich_print
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

console = Console()


def print_success(message: str) -> None:
    """Print a success message."""
    rich_print(f"[green]✓ {message}[/green]")


def print_error(message: str) -> None:
    """Print an error message."""
    rich_print(f"[red]✗ {message}[/red]")


def print_warning(message: str) -> None:
    """Print a warning message."""
    rich_print(f"[yellow]! {message}[/yellow]")


def print_info(message: str) -> None:
    """Print an info message."""
    rich_print(f"[blue]ℹ {message}[/blue]")


def print_header(title: str) -> None:
    """Print a header with emphasis."""
    rich_print(f"[bold blue]{title}[/bold blue]")


def print_section(title: str, content: str = "") -> None:
    """Print a section with title and optional content."""
    panel = Panel(
        content if content else "",
        title=f"[bold blue]{title}[/bold blue]",
        border_style="blue",
        expand=False,
    )
    console.print(panel)


def print_summary(title: str, items: list[tuple[str, Any]]) -> None:
    """Print a summary with key-value pairs."""
    panel_content = "\n".join([f"[cyan]{key}:[/cyan] {value}" for key, value in items])
    panel = Panel(
        panel_content,
        title=f"[bold]{title}[/bold]",
        border_style="magenta",
        expand=False,
    )
    console.print(panel)


def create_progress_bar() -> Progress:
    """Create a progress bar with consistent styling."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(
            bar_width=40, style="blue", complete_style="green", finished_style="green"
        ),
        TaskProgressColumn(),
        TextColumn("[progress.percentage]{task.completed}/{task.total}"),
    )


def create_backup_progress_bar() -> Progress:
    """Create a backup progress bar with consistent styling."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}", style="cyan"),
        BarColumn(
            bar_width=50,
            style="dim blue",
            complete_style="green",
            finished_style="green",
        ),
        TaskProgressColumn(style="bold"),
        TextColumn(
            "[progress.percentage]{task.completed}/{task.total} images", style="cyan"
        ),
    )


def print_provider_list(providers: list[tuple[str, str]]) -> None:
    """Print provider list in a clean format."""
    print_header("Available Providers")
    console.print()

    for status, name in providers:
        status_icon = "[green]✓[/green]" if "Enabled" in status else "[red]✗[/red]"
        status_color = "green" if "Enabled" in status else "red"
        console.print(
            f"{status_icon} {name} [{status_color}]({status})[/{status_color}]"
        )

    console.print()


def print_backup_summary(
    provider_name: str, success: int, error: int, skip: int
) -> None:
    """Print backup summary in a clean format."""
    total = success + error + skip

    items = [
        ("Successfully Downloaded", success),
        ("Failed Downloads", error),
        ("Skipped Files", skip),
        ("Total", total),
    ]

    print_summary(f"{provider_name} Backup Summary", items)

    if error > 0:
        console.print()
        print_warning(
            f"There are {error} failed downloads, please check network connection or provider configuration"
        )


def print_upload_summary(
    provider_name: str, success: int, error: int, total: int
) -> None:
    """Print upload summary in a clean format."""
    items = [
        ("Successfully Uploaded", success),
        ("Failed Uploads", error),
        ("Total Files", total),
    ]

    print_summary(f"{provider_name} Upload Summary", items)

    if error > 0:
        console.print()
        print_warning(
            f"There are {error} failed uploads, please check the logs for details"
        )


def print_compression_summary(success: int, error: int, skip: int, total: int) -> None:
    """Print compression summary in a clean format."""
    items = [
        ("Successfully Compressed", success),
        ("Failed Compressions", error),
        ("Skipped Files", skip),
        ("Total Files", total),
    ]

    print_summary("Compression Summary", items)

    if error > 0:
        console.print()
        print_warning(
            f"There are {error} failed compressions, please check the logs for details"
        )


def print_statistics(stats: dict[str, Any]) -> None:
    """Print backup statistics in a clean format."""
    print_header("Backup Statistics")
    console.print()

    console.print(f"[cyan]Total Operations:[/cyan] {stats['total_operations']}")
    console.print(
        f"[green]Successful Operations:[/green] {stats['successful_operations']}"
    )
    console.print(f"[red]Failed Operations:[/red] {stats['failed_operations']}")
    console.print(f"[cyan]Total Files:[/cyan] {stats['total_files']}")
    console.print(f"[cyan]Total Size:[/cyan] {stats['total_size']:,} bytes")

    if stats["operations_by_type"]:
        console.print()
        print_header("Operations by Type:")
        for op_type, count in stats["operations_by_type"].items():
            console.print(f"  {op_type}: {count}")


def print_history(records: list[Any]) -> None:
    """Print backup history records in a clean format."""
    if not records:
        print_warning("No backup records found")
        return

    print_header("Recent Backup Records")
    console.print()

    # Show last 20 records
    for record in records[:20]:
        status_color = "green" if record.status == "success" else "red"
        status_icon = "✓" if record.status == "success" else "✗"

        console.print(
            f"[cyan]{record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else 'Unknown'}[/cyan]"
        )
        console.print(f"  [magenta]Operation:[/magenta] {record.operation}")
        console.print(f"  [green]Provider:[/green] {record.provider}")
        console.print(f"  [yellow]File:[/yellow] {Path(record.file_path).name}")
        console.print(
            f"  [{status_color}]Status:[/{status_color}] [{status_color}]{status_icon} {record.status}[/{status_color}]"
        )
        console.print()


def print_duplicates(duplicates: dict[str, list[str]]) -> None:
    """Print duplicate files in a clean format."""
    if not duplicates:
        print_success("No duplicate files found")
        return

    print_header("Duplicate Files")
    console.print()

    # Show first 10 duplicates
    for file_hash, files in list(duplicates.items())[:10]:
        console.print(f"[cyan]Hash:[/cyan] {file_hash[:8]}...")
        for file_path in files:
            console.print(f"  [yellow]→[/yellow] {Path(file_path).name}")
        console.print()
