"""src/ui.py — Interface CLI estilo Claude Code (Rich + prompt-toolkit).

A função run_cli(engine) recebe o motor, exibe o banner, gerencia o loop de
input e despacha cada pergunta para engine.analyze().

Comandos de base : /help /status /about /clear /exit
Comandos extras  : /scan (nova leitura) · /cenario <nome> · /cenarios (lista)
"""

from datetime import datetime

import pyfiglet
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()
session = PromptSession(style=Style.from_dict({"prompt": "#06B6D4 bold"}))

# Paleta da CLI
CIANO = "#06B6D4"
ROXO = "#A855F7"
CINZA = "#8484A0"


def show_banner():
    """Exibe o banner ASCII colorido no início."""
    banner = pyfiglet.figlet_format("Mission Control", font="ansi_shadow")
    console.print(Text(banner, style=f"bold {CIANO}"))


def show_welcome(engine):
    """Painel de boas-vindas com comandos e status da conexão."""
    conectado = engine.api_key_presente() if hasattr(engine, "api_key_presente") else True
    subtitulo = "── connected ──" if conectado else "── sem OLLAMA_API_KEY ──"
    console.print(Panel.fit(
        "Bem-vindo à interface da [bold]Mission Control AI[/].\n"
        "Sistema de monitoramento e análise por IA generativa.\n"
        "Trilha: [bold]ConnectSat[/] · conectividade rural via satélite LEO.\n\n"
        "Use [bold]/help[/] para ver os comandos · [bold]/exit[/] para sair.\n"
        "Modelo: [bold]gpt-oss:120b[/] via Ollama Cloud",
        title=" ◆ MISSION CONTROL",
        subtitle=subtitulo,
        border_style=CIANO,
        padding=(1, 2),
    ))


def show_help():
    """Tabela de comandos disponíveis."""
    tabela = Table(title=None, border_style=CIANO, header_style=f"bold {CIANO}",
                   show_edge=True, pad_edge=False)
    tabela.add_column("Comando", style="bold")
    tabela.add_column("O que faz")
    tabela.add_row("/help", "Mostra esta lista de comandos")
    tabela.add_row("/status", "Telemetria atual + alertas + ações automáticas")
    tabela.add_row("/scan", "Coleta uma nova leitura no cenário atual")
    tabela.add_row("/cenario <nome>", "Troca o cenário simulado (ex.: /cenario bateria_critica)")
    tabela.add_row("/cenarios", "Lista os cenários disponíveis para teste")
    tabela.add_row("/about", "Sobre o projeto e a missão")
    tabela.add_row("/clear", "Limpa a tela e redesenha o banner")
    tabela.add_row("/exit", "Encerra a sessão")
    tabela.add_row("<pergunta>", "Qualquer outro texto vai para a análise da IA")
    console.print(tabela)


def show_about(engine):
    """Painel 'sobre'."""
    console.print(Panel(
        "[bold]Mission Control AI — Trilha ConnectSat[/]\n\n"
        "Monitora a telemetria de um satélite de telecomunicações em órbita "
        "baixa (LEO) que leva internet a regiões rurais. A lógica de alertas "
        "roda em Python; a IA generativa (gpt-oss:120b) explica cada anomalia "
        "e traduz o que ela significa para escolas, postos de saúde e pequenos "
        "negócios atendidos pelo feixe.\n\n"
        f"Trilha ativa: [bold]{getattr(engine, 'trilha', 'connectsat')}[/]\n"
        "Global Solution 2026.1 · Prompt Engineering and AI · FIAP",
        title=" ◆ Sobre", border_style=ROXO, padding=(1, 2),
    ))


def show_status(text):
    """Renderiza o status da telemetria como texto pré-formatado (preserva o
    alinhamento das colunas)."""
    now = datetime.now().strftime("%H:%M")
    console.print(Panel(Text(text), title=" ◆ Telemetria", subtitle=now,
                        border_style=ROXO, padding=(1, 2)))


def show_response(text):
    """Renderiza a resposta da IA em painel, interpretando o Markdown."""
    now = datetime.now().strftime("%H:%M")
    console.print(Panel(Markdown(text), title=" ◆ Mission Control AI",
                        subtitle=now, border_style=CIANO, padding=(1, 2)))


def _comando_cenario(engine, arg):
    """Trata '/cenario <nome>'."""
    disponiveis = engine.cenarios_disponiveis()
    if not arg:
        console.print(f"[yellow]Uso:[/] /cenario <nome>. Disponíveis: "
                      f"{', '.join(disponiveis)}")
        return
    if arg not in disponiveis:
        console.print(f"[red]Cenário '{arg}' não existe.[/] Disponíveis: "
                      f"{', '.join(disponiveis)}")
        return
    engine.atualizar_telemetria(arg)
    console.print(f"[green]Cenário alterado para[/] [bold]{arg}[/].")
    show_status(engine.status_snapshot())


def run_cli(engine):
    """Loop principal da CLI."""
    show_banner()
    show_welcome(engine)

    if not engine.is_ready():
        console.print(" ⚠ Engine status: AGUARDANDO IMPLEMENTAÇÃO ✗\n", style="yellow")
    else:
        console.print(" ✓ Engine status: ONLINE — análise conectada\n", style="green")

    while True:
        try:
            user_input = session.prompt(" ❯ ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue

        # Separa comando e argumento (ex.: "/cenario bateria_critica")
        partes = user_input.split(maxsplit=1)
        comando = partes[0].lower()
        arg = partes[1].strip() if len(partes) > 1 else ""

        if comando == "/exit":
            console.print("Encerrando a Mission Control AI. Até a próxima órbita. 🛰", style=CINZA)
            break
        if comando == "/help":
            show_help()
            continue
        if comando == "/about":
            show_about(engine)
            continue
        if comando == "/status":
            show_status(engine.status_snapshot())
            continue
        if comando == "/scan":
            engine.atualizar_telemetria()
            console.print("[green]Nova leitura coletada.[/]")
            show_status(engine.status_snapshot())
            continue
        if comando == "/cenarios":
            console.print("Cenários disponíveis: " +
                          ", ".join(engine.cenarios_disponiveis()))
            continue
        if comando == "/cenario":
            _comando_cenario(engine, arg)
            continue
        if comando == "/clear":
            console.clear()
            show_banner()
            show_welcome(engine)
            continue

        # Qualquer outra entrada vai para o motor de análise da IA.
        with console.status("[cyan]Consultando a IA…[/]", spinner="dots"):
            resposta = engine.analyze(user_input)
        show_response(resposta)
