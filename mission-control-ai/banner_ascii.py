"""banner_ascii.py — Gerador de banner ASCII (script auxiliar standalone).

Útil para experimentar fontes do PyFiglet e customizar o banner do projeto.

Uso:
    python banner_ascii.py                          # banner padrão
    python banner_ascii.py --fonts                  # lista as 500+ fontes
    python banner_ascii.py --font slant --text "Mission Control AI"
    python banner_ascii.py --demo                   # 8 fontes lado a lado
"""

import argparse

import pyfiglet
from rich.align import Align
from rich.console import Console
from rich.text import Text

console = Console()

FONTES_DEMO = [
    "ansi_shadow", "slant", "big", "standard",
    "banner3", "doom", "small", "block",
]


def banner_padrao():
    """Gera as duas linhas do banner em ASCII art (identidade do projeto)."""
    linha1 = pyfiglet.figlet_format("Global Solution", font="ansi_shadow")
    linha2 = pyfiglet.figlet_format("Mission Control AI", font="ansi_shadow")
    console.print(Align.center(Text(linha1, style="bold #A855F7")))
    console.print(Align.center(Text(linha2, style="bold #06B6D4")))
    console.print(Align.center(
        Text(" ── 2026.1 · Prompt Engineering and AI · FIAP ── ",
             style="italic #8484A0")
    ))


def listar_fontes():
    fontes = sorted(pyfiglet.FigletFont.getFonts())
    console.print(f"[bold]{len(fontes)} fontes disponíveis no PyFiglet:[/]\n")
    console.print(", ".join(fontes))


def testar_fonte(fonte, texto):
    try:
        arte = pyfiglet.figlet_format(texto, font=fonte)
    except pyfiglet.FontNotFound:
        console.print(f"[red]Fonte '{fonte}' não encontrada.[/] "
                      "Use --fonts para ver as disponíveis.")
        return
    console.print(Text(arte, style="bold #06B6D4"))


def demo():
    for fonte in FONTES_DEMO:
        console.rule(f"[bold #A855F7]{fonte}")
        try:
            console.print(Text(pyfiglet.figlet_format("Mission Control AI", font=fonte),
                               style="bold #06B6D4"))
        except pyfiglet.FontNotFound:
            console.print(f"[red](fonte '{fonte}' indisponível)[/]")


def main():
    parser = argparse.ArgumentParser(description="Gerador de banner ASCII da Mission Control AI.")
    parser.add_argument("--fonts", action="store_true", help="Lista as fontes disponíveis")
    parser.add_argument("--font", type=str, help="Testa uma fonte específica")
    parser.add_argument("--text", type=str, default="Mission Control AI", help="Texto do banner")
    parser.add_argument("--demo", action="store_true", help="Mostra 8 fontes lado a lado")
    args = parser.parse_args()

    if args.fonts:
        listar_fontes()
    elif args.demo:
        demo()
    elif args.font:
        testar_fonte(args.font, args.text)
    else:
        banner_padrao()


if __name__ == "__main__":
    main()
