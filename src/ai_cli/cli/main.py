"""
Command Line Interface for AI CLI application.
"""

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text

from ..config.settings import AppConfig
from ..core.exceptions import (
    AICliError,
    AIServiceError,
    ConfigurationError,
    GitError,
    NoStagedChangesError,
    PullRequestError,
    RepositoryError,
)
from ..core.models import Repository, RepositoryVisibility
from ..infrastructure.ai_service import GeminiAIService
from ..infrastructure.git_repository import GitRepository
from ..infrastructure.pr_service import GitHubPRService
from ..infrastructure.repo_service import GitHubRepoService
from ..services.create_pr_service import CreatePRService
from ..services.smart_commit_all_service import SmartCommitAllService
from ..services.smart_commit_service import SmartCommitService

console = Console()
app = typer.Typer(
    name="ai-cli",
    help="AI-powered git commit and PR creation tool",
    rich_markup_mode="rich",
)


class CLIController:
    """Controller for CLI operations."""

    def __init__(self):
        try:
            self.config = AppConfig.load()
            self._setup_services()
        except ConfigurationError as e:
            console.print(f"[bold red]Configuration Error:[/bold red] {e}")
            raise typer.Exit(1) from None

    def _setup_services(self):
        """Setup all services."""
        self.git_repo = GitRepository(self.config.git)
        self.ai_service = GeminiAIService(self.config.ai)

        try:
            self.pr_service = GitHubPRService()
        except PullRequestError as e:
            if self.config.debug:
                console.print(f"[yellow]Warning:[/yellow] {e}")
            self.pr_service = None

        self.smart_commit_service = SmartCommitService(
            git_repo=self.git_repo,
            ai_service=self.ai_service,
            pr_service=self.pr_service,
        )

    def handle_smart_commit(
        self, push: bool = True, pr: bool = False, auto_confirm: bool = False
    ):
        """Handle smart commit command."""
        try:
            console.print("[yellow]🔍 Analyzing staged changes...[/yellow]")

            diff = self.smart_commit_service.get_staged_changes()

            if diff.is_truncated:
                console.print(
                    "[yellow]⚠️  Large diff detected - truncated for AI analysis[/yellow]"
                )

            console.print("[yellow]🤖 Generating commit message with AI...[/yellow]")
            commit_msg = self.smart_commit_service.generate_commit_message(diff)

            panel = Panel(
                Text(commit_msg, style="bold green"),
                title="💡 Suggested Commit Message",
                border_style="green",
            )
            console.print(panel)

            # Confirm with user
            if not auto_confirm and not Confirm.ask("✅ Accept this message?"):
                commit_msg = typer.prompt("📝 Enter your custom message")

            # Create commit
            console.print("[yellow]📦 Creating commit...[/yellow]")
            self.smart_commit_service.create_commit(commit_msg)
            console.print("[bold green]✅ Commit created successfully![/bold green]")

            # Push if requested
            if push:
                current_branch = self.git_repo.get_current_branch()
                console.print(
                    f"[yellow]🚀 Pushing to branch '{current_branch.name}'...[/yellow]"
                )
                self.smart_commit_service.push_changes(True)
                console.print(
                    "[bold green]✅ Changes pushed successfully![/bold green]"
                )

            # Create PR if requested
            if pr:
                if not self.pr_service:
                    console.print(
                        "[bold red]❌ Pull Request creation not available. "
                        "Make sure GitHub CLI is installed and configured.[/bold red]"
                    )
                    return

                console.print("[yellow]📋 Generating pull request...[/yellow]")
                pr_data = self.ai_service.generate_pull_request(diff, commit_msg)

                # Display PR preview
                pr_panel = Panel(
                    f"[bold]Title:[/bold] {pr_data.title}\n\n[bold]Description:[/bold]\n{pr_data.body}",
                    title="📋 Pull Request Preview",
                    border_style="blue",
                )
                console.print(pr_panel)

                if auto_confirm or Confirm.ask(
                    "🚀 Create pull request with this content?"
                ):
                    self.pr_service.create_pull_request(pr_data)
                    console.print(
                        "[bold green]✅ Pull request created successfully![/bold green]"
                    )
                else:
                    console.print("[yellow]ℹ️  Pull request creation skipped.[/yellow]")

        except NoStagedChangesError:
            console.print(
                "[bold red]❌ No staged changes found.[/bold red]\n"
                "[yellow]💡 Use 'git add' to stage your changes first.[/yellow]"
            )
            raise typer.Exit(1) from None

        except GitError as e:
            console.print(f"[bold red]Git Error:[/bold red] {e}")
            raise typer.Exit(1) from None

        except AIServiceError as e:
            console.print(f"[bold red]AI Service Error:[/bold red] {e}")
            raise typer.Exit(1) from None

        except PullRequestError as e:
            console.print(f"[bold red]Pull Request Error:[/bold red] {e}")
            raise typer.Exit(1) from None

        except AICliError as e:
            console.print(f"[bold red]Application Error:[/bold red] {e}")
            raise typer.Exit(1) from None

        except Exception as e:
            console.print(f"[bold red]Unexpected Error:[/bold red] {e}")
            if self.config.debug:
                import traceback

                console.print("[dim]Debug traceback:[/dim]")
                console.print(traceback.format_exc())
            raise typer.Exit(1) from None


# Global controller instance
cli_controller: Optional[CLIController] = None


def get_cli_controller() -> CLIController:
    """Get or create CLI controller instance."""
    global cli_controller
    if cli_controller is None:
        cli_controller = CLIController()
    return cli_controller


@app.command()
def smart_commit(
    push: bool = typer.Option(
        True, "--push/--no-push", help="Push changes to remote repository"
    ),
    pr: bool = typer.Option(
        False, "--pr/--no-pr", help="Create pull request after commit"
    ),
    auto_confirm: bool = typer.Option(
        False, "--yes", "-y", help="Auto-confirm all prompts"
    ),
):
    """
    🚀 Create AI-powered commit with optional push and PR creation.

    This command will:
    1. 🔍 Analyze your staged changes
    2. 🤖 Generate a conventional commit message using AI
    3. 📦 Create the commit
    4. 🚀 Push to remote (if --push, default: true)
    5. 📋 Create pull request (if --pr, default: false)
    """
    controller = get_cli_controller()
    controller.handle_smart_commit(push=push, pr=pr, auto_confirm=auto_confirm)


@app.command()
def version():
    """Show version information."""
    console.print("[bold green]AI CLI[/bold green] v0.1.0")
    console.print("🤖 AI-powered git commit and PR creation tool")


@app.command()
def setup(
    api_key: str = typer.Option(
        None,
        "--api-key",
        "-k",
        help="Set the GEMINI_API_KEY directly (skips interactive prompt)",
    ),
):
    """
    ⚙️ Configure ai-cli with your API key.

    This command helps you set up ai-cli by configuring your GEMINI_API_KEY
    in the global config (~/.config/ai-cli/.env).

    Examples:
        ai-cli setup                          # Interactive setup
        ai-cli setup --api-key YOUR_KEY       # Set API key directly
    """
    from pathlib import Path

    global_path = Path.home() / ".config" / "ai-cli" / ".env"
    global_path.parent.mkdir(parents=True, exist_ok=True)

    def get_current_key() -> str:
        if not global_path.exists():
            return ""
        try:
            for line in global_path.read_text().split("\n"):
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip()
        except Exception:
            pass
        return ""

    def save_api_key(key: str) -> None:
        if global_path.exists():
            content = global_path.read_text()
            lines = content.split("\n")
            updated = False
            for i, line in enumerate(lines):
                if line.startswith("GEMINI_API_KEY="):
                    lines[i] = f"GEMINI_API_KEY={key}"
                    updated = True
                    break
            if updated:
                global_path.write_text("\n".join(lines))
                return
        # Create new file
        global_path.write_text(f"GEMINI_API_KEY={key}\n")

    # Direct API key provided
    if api_key:
        save_api_key(api_key)
        console.print(f"[bold green]✅ API key saved to {global_path}[/bold green]")
        return

    # Interactive setup
    console.print("[bold]🤖 AI CLI Setup[/bold]")
    console.print("=" * 40)

    current_key = get_current_key()
    if current_key:
        masked = (
            current_key[:8] + "..." + current_key[-4:]
            if len(current_key) > 12
            else "***"
        )
        console.print(f"\nCurrent API key: [dim]{masked}[/dim]")
        if not typer.confirm("\nUpdate API key?", default=False):
            console.print("[yellow]No changes made.[/yellow]")
            return

    console.print("\n[blue]Get your API key from:[/blue]")
    console.print(
        "[link=https://makersuite.google.com/app/apikey]https://makersuite.google.com/app/apikey[/link]\n"
    )

    new_key = typer.prompt("Enter your GEMINI_API_KEY")
    if not new_key.strip():
        console.print("[bold red]❌ No API key provided. Aborted.[/bold red]")
        raise typer.Exit(1)

    save_api_key(new_key.strip())
    console.print(f"\n[bold green]✅ API key saved to {global_path}[/bold green]")
    console.print(
        "\n[bold]🎉 Setup complete![/bold] You can now use ai-cli from any project.\n"
    )
    console.print("[dim]Quick start:[/dim]")
    console.print("  ai-cli smart-commit      [dim]# AI-powered commit[/dim]")
    console.print("  ai-cli create-pr         [dim]# Create PR from branch[/dim]")
    console.print("  ai-cli --help            [dim]# See all commands[/dim]")


def _get_config_value(config_path, key: str) -> str:
    """Read a config value from a .env file."""
    if not config_path.exists():
        return ""
    try:
        for line in config_path.read_text().split("\n"):
            if line.startswith(f"{key}="):
                value = line.split("=", 1)[1].strip()
                # Remove quotes if present
                if (
                    value.startswith('"')
                    and value.endswith('"')
                    or value.startswith("'")
                    and value.endswith("'")
                ):
                    value = value[1:-1]
                return value
    except Exception:
        pass
    return ""


def _set_config_value(config_path, key: str, value: str) -> None:
    """Set or update a config value in a .env file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if config_path.exists():
        content = config_path.read_text()
        lines = content.split("\n")
        updated = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f'{key}="{value}"'
                updated = True
                break
        if updated:
            config_path.write_text("\n".join(lines))
            return
        # Key not found, append it
        if lines and lines[-1]:
            lines.append("")
        lines.append(f'{key}="{value}"')
        config_path.write_text("\n".join(lines))
    else:
        config_path.write_text(f'{key}="{value}"\n')


@app.command()
def config(
    set_model: str = typer.Option(
        None, "--model", "-m", help="Set the AI model to use"
    ),
    use_global: bool = typer.Option(
        False, "--global", "-g", help="Apply changes to global config"
    ),
    select_model: bool = typer.Option(
        False, "--select", "-s", help="Interactive model selection from history"
    ),
):
    """
    🔧 Show or update ai-cli configuration.

    Examples:
        ai-cli config                    # Show current config
        ai-cli config --select           # Interactive model selection
        ai-cli config --model gemini-2.0-flash  # Change model directly
        ai-cli config --model gemini-2.0-flash --global  # Change model globally
    """
    from pathlib import Path

    from ..config.cache import get_cache

    global_path = Path.home() / ".config" / "ai-cli" / ".env"
    local_path = Path(".env")

    # Determine active config (local takes priority)
    active_path = local_path if local_path.exists() and not use_global else global_path
    cache = get_cache()

    # Interactive model selection
    if select_model:
        _interactive_model_select(active_path, cache)
        return

    # If setting model directly, update and exit
    if set_model:
        _set_config_value(active_path, "MODEL_NAME", set_model)
        cache.add_model_to_history(set_model)
        console.print(f"[bold green]✅ Model set to:[/bold green] {set_model}")
        console.print(f"[dim]   Saved to: {active_path}[/dim]")
        return

    # Show config status
    _show_config_status(global_path, local_path)


def _interactive_model_select(active_path, cache) -> None:
    """Interactive model selection with arrow keys navigation."""
    from rich.table import Table

    models = cache.get_model_history()
    current_model = _get_config_value(active_path, "MODEL_NAME") or "gemini-2.0-flash"
    selected_idx = 0

    # Find current model index
    for i, model in enumerate(models):
        if model == current_model:
            selected_idx = i
            break

    def render_table(models_list: list[str], sel_idx: int, curr_model: str) -> Table:
        """Render the model selection table."""
        table = Table(show_header=True, header_style="bold", title="🤖 Select AI Model")
        table.add_column("#", style="dim", width=3)
        table.add_column("Model")
        table.add_column("Status", width=12)

        for i, model in enumerate(models_list):
            prefix = "→ " if i == sel_idx else "  "
            # Use Text object to avoid markup issues with model names
            if i == sel_idx:
                model_text = Text(model, style="bold reverse cyan")
            else:
                model_text = Text(model, style="cyan")
            status = "[green]● current[/green]" if model == curr_model else ""
            table.add_row(f"{prefix}{i + 1}", model_text, status)

        return table

    while True:
        # Clear and render
        console.clear()
        console.print(render_table(models, selected_idx, current_model))
        console.print(
            "\n[dim]↑/↓: Navigate | Enter: Select | n: New | d: Delete | q: Quit[/dim]"
        )

        # Get single keypress
        key = _get_keypress()

        if key in ("q", "Q", "\x1b"):  # q or Escape
            console.print("[yellow]Cancelled.[/yellow]")
            return

        if key in ("\r", "\n") and models:  # Enter
            selected = models[selected_idx]
            cache.add_model_to_history(selected)
            _set_config_value(active_path, "MODEL_NAME", selected)
            console.print(f"\n[bold green]✅ Model set to:[/bold green] {selected}")
            return

        if key in ("k", "K", "\x1b[A"):  # Up arrow or k
            selected_idx = (selected_idx - 1) % len(models) if models else 0

        if key in ("j", "J", "\x1b[B"):  # Down arrow or j
            selected_idx = (selected_idx + 1) % len(models) if models else 0

        if key in ("n", "N"):  # New model
            console.print("\n[bold]Add New Model[/bold]")
            new_model = typer.prompt("Enter model name (empty to cancel)", default="")
            if new_model.strip():
                cache.add_model_to_history(new_model.strip())
                _set_config_value(active_path, "MODEL_NAME", new_model.strip())
                console.print(
                    f"\n[bold green]✅ Model set to:[/bold green] {new_model.strip()}"
                )
                return
            # Refresh models list
            models = cache.get_model_history()

        if key in ("d", "D"):  # Delete
            if models and len(models) > 1:
                model_to_delete = models[selected_idx]
                console.print(
                    f"\n[bold yellow]Delete model:[/bold yellow] {model_to_delete}"
                )
                if typer.confirm("Are you sure?", default=False):
                    cache.remove_model_from_history(model_to_delete)
                    models = cache.get_model_history()
                    selected_idx = min(selected_idx, len(models) - 1)
                    console.print(f"[yellow]Removed:[/yellow] {model_to_delete}")
            elif models:
                console.print("\n[red]Cannot delete the last model.[/red]")
                typer.prompt("Press Enter to continue", default="")


def _get_keypress() -> str:
    """Get a single keypress from the user."""
    import sys
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                return f"\x1b[{ch3}"
            return ch
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _show_config_status(global_path, local_path) -> None:
    """Show current configuration status."""
    console.print("[bold]🔧 AI CLI Configuration[/bold]\n")

    active_path = local_path if local_path.exists() else global_path
    active_label = "local" if local_path.exists() else "global"

    api_key = _get_config_value(active_path, "GEMINI_API_KEY")
    model_name = _get_config_value(active_path, "MODEL_NAME") or "gemini-2.0-flash"

    console.print("[bold]Current Settings:[/bold]")
    if api_key:
        masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        console.print(f"  API Key: [green]{masked}[/green]")
    else:
        console.print("  API Key: [red]Not set[/red]")

    console.print(f"  Model:   [cyan]{model_name}[/cyan]")
    console.print(f"  Source:  [dim]{active_label} ({active_path})[/dim]")

    # Show config files status
    console.print("\n[bold]Config Files:[/bold]")
    if global_path.exists():
        console.print(f"  [green]✓[/green] Global: {global_path}")
    else:
        console.print(f"  [dim]✗[/dim] Global: {global_path} [dim](not found)[/dim]")

    if local_path.exists():
        console.print(f"  [green]✓[/green] Local:  {local_path.absolute()}")
        console.print("    [dim](takes priority over global)[/dim]")
    else:
        console.print("[dim]  ✗ Local:  .env (not found)[/dim]")

    console.print("\n[dim]Commands:[/dim]")
    console.print("  ai-cli setup              [dim]# Change API key[/dim]")
    console.print("  ai-cli config -s          [dim]# Select model (interactive)[/dim]")
    console.print("  ai-cli config -m MODEL    [dim]# Set model directly[/dim]")


@app.command()
def create_repo(
    name: str = typer.Argument(..., help="Name of the repository to create"),
    visibility: str = typer.Option(
        "private",
        "--visibility",
        "-v",
        help="Repository visibility: public, private, or internal",
    ),
    description: str = typer.Option(
        "",
        "--description",
        "-d",
        help="Repository description",
    ),
):
    """
    📁 Create a new GitHub repository.

    This command will create a new repository on GitHub using the GitHub CLI.

    Examples:
        ai-cli create-repo my-new-project
        ai-cli create-repo my-app -v public -d "My awesome application"
    """
    try:
        # Validate visibility
        try:
            repo_visibility = RepositoryVisibility(visibility.lower())
        except ValueError:
            console.print(
                f"[bold red]❌ Invalid visibility '{visibility}'.[/bold red]\n"
                "[yellow]💡 Valid options: public, private, internal[/yellow]"
            )
            raise typer.Exit(1) from None

        console.print(f"[yellow]📁 Creating repository '{name}'...[/yellow]")

        repo_service = GitHubRepoService()
        repo = Repository(
            name=name,
            visibility=repo_visibility,
            description=description,
        )

        url = repo_service.create_repository(repo)

        console.print("[bold green]✅ Repository created successfully![/bold green]")
        console.print(f"[blue]🔗 URL: {url}[/blue]")

    except RepositoryError as e:
        console.print(f"[bold red]Repository Error:[/bold red] {e}")
        raise typer.Exit(1) from None

    except Exception as e:
        console.print(f"[bold red]Unexpected Error:[/bold red] {e}")
        raise typer.Exit(1) from None


@app.command()
def smart_commit_all(
    push: bool = typer.Option(
        True, "--push/--no-push", help="Push changes to remote repository"
    ),
    auto_confirm: bool = typer.Option(
        False, "--yes", "-y", help="Auto-confirm all prompts"
    ),
):
    """
    🚀 Commit ALL changes in the project with smart grouping.

    This command will:
    1. 🔍 Find all changed files in the repository
    2. 📁 Group files by folder
    3. 🔗 Analyze file correlation within each folder
    4. 🤖 Generate commit messages for each group
    5. 📦 Create separate commits for each group
    6. 🚀 Push to remote (if --push, default: true)

    Files in the same folder that are related (e.g., a module and its tests)
    will be committed together. Unrelated files will be committed separately.
    """
    try:
        config = AppConfig.load()
        git_repo = GitRepository(config.git)
        ai_service = GeminiAIService(config.ai)

        service = SmartCommitAllService(git_repo=git_repo, ai_service=ai_service)

        # Get all changes first
        console.print("[yellow]🔍 Scanning for all changes...[/yellow]")
        changes = service.get_all_changes()

        if not changes:
            console.print(
                "[bold yellow]⚠️  No changes found in the repository.[/bold yellow]"
            )
            raise typer.Exit(0) from None

        console.print(f"\n[bold]Found {len(changes)} changed file(s):[/bold]")
        for change in changes:
            status_icon = {
                "M": "📝",
                "A": "➕",
                "D": "❌",
                "R": "🔄",
                "??": "❓",
            }.get(change.status, "📄")
            console.print(f"  {status_icon} {change.path} ({change.status})")

        if not auto_confirm and not Confirm.ask("\n✅ Proceed with smart commit all?"):
            console.print("[yellow]ℹ️  Operation cancelled.[/yellow]")
            raise typer.Exit(0) from None

        console.print("\n[yellow]🤖 Analyzing and grouping files...[/yellow]")
        result = service.execute_smart_commit_all(auto_push=push)

        console.print("\n[bold]📊 Commit Summary:[/bold]")
        for commit in result.commits:
            if commit.success:
                console.print(
                    f"\n[green]✅ {commit.folder}/[/green] ({len(commit.files)} file(s))"
                )
                console.print(f"   [dim]Message:[/dim] {commit.commit_message}")
                for f in commit.files:
                    console.print(f"   • {f}")
            else:
                console.print(f"\n[red]❌ {commit.folder}/[/red] - {commit.error}")

        console.print("\n" + "─" * 50)
        console.print(
            f"[bold]Total:[/bold] {result.total_files} files in {result.total_commits} commits"
        )
        console.print(
            f"[green]Successful:[/green] {result.successful_commits} | [red]Failed:[/red] {result.failed_commits}"
        )

        if result.pushed:
            console.print(
                "[bold green]✅ All changes pushed successfully![/bold green]"
            )
        elif push and result.successful_commits > 0:
            console.print("[bold yellow]⚠️  Push failed[/bold yellow]")

    except ConfigurationError as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        raise typer.Exit(1) from None

    except GitError as e:
        console.print(f"[bold red]Git Error:[/bold red] {e}")
        raise typer.Exit(1) from None

    except AIServiceError as e:
        console.print(f"[bold red]AI Service Error:[/bold red] {e}")
        raise typer.Exit(1) from None

    except AICliError as e:
        console.print(f"[bold red]Application Error:[/bold red] {e}")
        raise typer.Exit(1) from None


@app.command()
def create_pr(
    base: str = typer.Option(
        None,
        "--base",
        "-b",
        help="Base branch to create PR against (default: main/master)",
    ),
    auto_confirm: bool = typer.Option(
        False, "--yes", "-y", help="Auto-confirm PR creation"
    ),
):
    """
    📋 Create a Pull Request based on current branch changes.

    This command will:
    1. 🔍 Analyze commits on the current branch
    2. 📊 Compare changes against base branch (main/master)
    3. 🤖 Generate PR title and description using AI
    4. 📋 Create the Pull Request on GitHub

    Examples:
        ai-cli create-pr
        ai-cli create-pr --base develop
        ai-cli create-pr --yes
    """
    try:
        config = AppConfig.load()
        git_repo = GitRepository(config.git)
        ai_service = GeminiAIService(config.ai)

        try:
            pr_service = GitHubPRService()
        except PullRequestError as e:
            console.print(f"[bold red]❌ GitHub CLI Error:[/bold red] {e}")
            raise typer.Exit(1) from None

        service = CreatePRService(
            git_repo=git_repo,
            ai_service=ai_service,
            pr_service=pr_service,
        )

        # Get branch info
        console.print("[yellow]🔍 Analyzing branch changes...[/yellow]")

        try:
            branch_info = service.get_branch_info(base)
        except GitError as e:
            console.print(f"[bold red]❌ {e}[/bold red]")
            raise typer.Exit(1) from None

        # Display branch summary
        console.print(f"\n[bold]Branch:[/bold] {branch_info.name}")
        console.print(f"[bold]Base:[/bold] {branch_info.base_branch}")
        console.print(f"[bold]Commits:[/bold] {len(branch_info.commits)}")
        console.print(f"[bold]Files Changed:[/bold] {len(branch_info.files_changed)}")

        # Show commits
        if branch_info.commits:
            console.print("\n[bold]📝 Commits:[/bold]")
            for commit in branch_info.commits[:10]:
                console.print(f"  • {commit}")
            if len(branch_info.commits) > 10:
                console.print(
                    f"  [dim]... and {len(branch_info.commits) - 10} more[/dim]"
                )

        # Show files changed
        if branch_info.files_changed:
            console.print("\n[bold]📁 Files Changed:[/bold]")
            for file in branch_info.files_changed[:10]:
                console.print(f"  • {file}")
            if len(branch_info.files_changed) > 10:
                console.print(
                    f"  [dim]... and {len(branch_info.files_changed) - 10} more[/dim]"
                )

        # Generate PR content
        console.print("\n[yellow]🤖 Generating PR content with AI...[/yellow]")
        pr = service.generate_pr_content(branch_info)

        # Display PR preview
        pr_panel = Panel(
            f"[bold]Title:[/bold] {pr.title}\n\n[bold]Description:[/bold]\n{pr.body}",
            title="📋 Pull Request Preview",
            border_style="blue",
        )
        console.print(pr_panel)

        # Confirm and create
        if not auto_confirm and not Confirm.ask("\n🚀 Create this Pull Request?"):
            console.print("[yellow]ℹ️  PR creation cancelled.[/yellow]")
            raise typer.Exit(0) from None

        console.print("\n[yellow]📤 Creating Pull Request...[/yellow]")
        pr_service.create_pull_request(pr)
        console.print("[bold green]✅ Pull Request created successfully![/bold green]")

    except ConfigurationError as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        raise typer.Exit(1) from None

    except PullRequestError as e:
        console.print(f"[bold red]PR Error:[/bold red] {e}")
        raise typer.Exit(1) from None

    except AIServiceError as e:
        console.print(f"[bold red]AI Service Error:[/bold red] {e}")
        raise typer.Exit(1) from None

    except AICliError as e:
        console.print(f"[bold red]Application Error:[/bold red] {e}")
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
