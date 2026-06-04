"""Mission Control AI — ponto de entrada do sistema."""

from src.engine import MissionEngine
from src.ui import run_cli

if __name__ == "__main__":
    engine = MissionEngine()
    run_cli(engine)
