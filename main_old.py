import typer
import subprocess
import os
import google.generativeai as genai
from rich.console import Console
from rich.prompt import Confirm

API_KEY = os.getenv("GEMINI_API_KEY")

console = Console()
app = typer.Typer()

if not API_KEY:
    console.print("[bold red]Erro: Variável de ambiente GEMINI_API_KEY não encontrada.[/bold red]")
    raise typer.Exit()

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction="You are a senior DevOps engineer obsessed with best practices and Conventional Commits."
)


def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def generate_ai_content(prompt, context):
    """Função adaptada para o Google Gemini."""
    try:
        full_prompt = f"{prompt}\n\nCONTEXT:\n{context}"

        response = model.generate_content(full_prompt)
        return response.text.strip()

    except Exception as e:
        console.print(f"[bold red]Erro na API do Gemini:[/bold red] {e}")
        raise typer.Exit()


@app.command()
def smart_commit(push: bool = True, pr: bool = False):
    """
    Gera commit message baseada em stage, faz push e opcionalmente abre PR.
    """

    # 1. Pegar alterações em 'stage'
    diff = run_command("git diff --cached")

    if not diff:
        console.print("[bold red]Nenhuma alteração em 'stage'. Use 'git add' primeiro.[/bold red]")
        raise typer.Exit()

    # Se o diff for muito grande, trunque para economizar tokens
    if len(diff) > 10000:
        diff = diff[:10000] + "\n...[TRUNCATED]"

    # 2. Gerar Mensagem de Commit
    console.print("[yellow]Gerando mensagem de commit com IA...[/yellow]")
    commit_prompt = """
    Gere uma mensagem de commit seguindo o padrão 'Conventional Commits'.
    Formato: <type>(<scope>): <subject>
    Exemplo: feat(auth): add login validation
    Apenas retorne a mensagem, sem aspas ou explicações extras.
    """
    commit_msg = generate_ai_content(commit_prompt, diff)

    console.print(f"\n[bold green]Sugestão:[/bold green] {commit_msg}")

    if not Confirm.ask("Aceitar esta mensagem?"):
        commit_msg = typer.prompt("Digite sua mensagem manual")

    run_command(f'git commit -m "{commit_msg}"')
    console.print("[bold blue]Commit realizado![/bold blue]")

    if push:
        branch = run_command("git branch --show-current")
        console.print(f"[yellow]Fazendo push para a branch {branch}...[/yellow]")
        run_command(f"git push origin {branch}")
        console.print("[bold blue]Push realizado![/bold blue]")

    if pr:
        create_pr(diff, commit_msg)

def create_pr(diff, commit_msg):
    console.print("\n[yellow]Gerando descrição do PR...[/yellow]")

    pr_prompt = """
    Crie um título e uma descrição para um Pull Request baseados nas alterações.
    O formato deve ser Markdown.
    Estrutura obrigatória:
    Title: [Sugestão de titulo curto]
    Body:
    ## O que foi feito
    - Tópicos claros
    ## Por que foi feito
    - Justificativa técnica
    ## Como testar
    - Passos breves
    """

    ai_response = generate_ai_content(pr_prompt, f"Commit Msg: {commit_msg}\n\nDiff: {diff}")

    lines = ai_response.split('\n')
    title = lines[0].replace("Title:", "").strip()
    body = "\n".join(lines[1:]).replace("Body:", "").strip()

    console.print(f"\n[bold]Título PR:[/bold] {title}")
    console.print("[bold]Descrição:[/bold]")
    console.print(body)

    if Confirm.ask("Abrir PR no GitHub com estes dados?"):
        body_escaped = body.replace('"', '\\"')
        cmd = f'gh pr create --title "{title}" --body "{body_escaped}" --web'
        os.system(cmd)


if __name__ == "__main__":
    app()