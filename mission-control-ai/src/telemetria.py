"""src/telemetria.py — Geração de dados simulados da Trilha ConnectSat.

Satélite simulado: nó de telecomunicações em órbita baixa (LEO), estilo
Starlink / OneWeb. Os parâmetros monitorados são específicos da trilha de
conectividade rural:

    - latencia_uplink_ms      latência de uplink (ms)
    - throughput_feixe_mbps   throughput do feixe (Mbps)
    - saude_antena_pct        saúde da antena phased-array (%)
    - erro_beam_steering_deg  erro de apontamento do beam steering (graus)
    - temp_transponder_c      carga térmica do transponder (°C)
    - bateria_pct             estado de carga da bateria (%)   [energia]
    - snr_db                  relação sinal-ruído do enlace (dB)
    - usuarios_conectados     usuários conectados ao feixe (contexto de impacto)

Os dados não precisam ser cientificamente exatos — precisam ser plausíveis e
coerentes com um satélite de telecom LEO. A geração é aleatória dentro de
faixas nominais, e pode ser forçada para um "cenário" (ex.: sobreaquecimento)
para testar os alertas e a análise da IA.
"""

import json
import random
from datetime import datetime, timezone
from pathlib import Path

# Identificação do ativo simulado — só para dar contexto à narrativa.
SATELITE = "CONNECTSAT-07 (LEO · 550 km)"

# Raiz do projeto (… /mission-control-ai), calculada a partir deste arquivo,
# para que o carregamento de data/cenarios.json funcione independente do CWD.
ROOT = Path(__file__).resolve().parent.parent
CENARIOS_PATH = ROOT / "data" / "cenarios.json"

# ---------------------------------------------------------------------------
# Faixas NOMINAIS de operação (estado saudável). A geração aleatória amostra
# dentro destas faixas. Valores inteiros (ex.: usuários) usam randint.
# ---------------------------------------------------------------------------
FAIXAS_NOMINAIS = {
    "latencia_uplink_ms":     {"faixa": (22.0, 45.0),   "unidade": "ms",       "rotulo": "Latência de uplink"},
    "throughput_feixe_mbps":  {"faixa": (180.0, 240.0), "unidade": "Mbps",     "rotulo": "Throughput do feixe"},
    "saude_antena_pct":       {"faixa": (92.0, 100.0),  "unidade": "%",        "rotulo": "Saúde da antena phased-array"},
    "erro_beam_steering_deg": {"faixa": (0.00, 0.15),   "unidade": "°",        "rotulo": "Erro de beam steering"},
    "temp_transponder_c":     {"faixa": (28.0, 52.0),   "unidade": "°C",       "rotulo": "Carga térmica do transponder"},
    "bateria_pct":            {"faixa": (75.0, 100.0),  "unidade": "%",        "rotulo": "Bateria"},
    "snr_db":                 {"faixa": (14.0, 22.0),   "unidade": "dB",       "rotulo": "Relação sinal-ruído (SNR)"},
    "usuarios_conectados":    {"faixa": (3500, 6200),   "unidade": "usuários", "rotulo": "Usuários conectados"},
}

# ---------------------------------------------------------------------------
# Cenários embutidos (fallback). Cada cenário sobrescreve alguns parâmetros.
# Valor [lo, hi] -> amostrado aleatoriamente nessa faixa; valor escalar -> fixo.
# data/cenarios.json, se existir, COMPLEMENTA / SOBRESCREVE estes.
# ---------------------------------------------------------------------------
CENARIOS_PADRAO = {
    "nominal": {},  # tudo dentro do normal — operação saudável

    "sobreaquecimento_transponder": {
        "temp_transponder_c": [78.0, 94.0],
        "throughput_feixe_mbps": [90.0, 140.0],
        "usuarios_conectados": [1800, 3200],
    },
    "degradacao_antena": {
        "saude_antena_pct": [55.0, 80.0],
        "throughput_feixe_mbps": [110.0, 160.0],
        "snr_db": [8.0, 12.0],
        "usuarios_conectados": [1500, 3000],
    },
    "perda_apontamento": {
        "erro_beam_steering_deg": [0.45, 1.20],
        "throughput_feixe_mbps": [70.0, 130.0],
        "usuarios_conectados": [400, 1500],
    },
    "bateria_critica": {  # eclipse orbital prolongado
        "bateria_pct": [8.0, 19.0],
        "throughput_feixe_mbps": [120.0, 170.0],
        "usuarios_conectados": [1200, 2600],
    },
    "congestionamento": {  # pico de demanda no feixe
        "latencia_uplink_ms": [95.0, 180.0],
        "throughput_feixe_mbps": [80.0, 130.0],
        "snr_db": [9.0, 13.0],
        "usuarios_conectados": [6000, 7800],
    },
    "blackout_total": {  # falha múltipla — teste de caso extremo
        "throughput_feixe_mbps": 0.0,
        "snr_db": 2.0,
        "saude_antena_pct": 35.0,
        "erro_beam_steering_deg": 1.8,
        "usuarios_conectados": 0,
    },
}


def _carregar_cenarios():
    """Mescla os cenários do arquivo data/cenarios.json (se existir) sobre os
    cenários padrão embutidos. O arquivo é OPCIONAL."""
    cenarios = dict(CENARIOS_PADRAO)
    try:
        if CENARIOS_PATH.exists():
            do_arquivo = json.loads(CENARIOS_PATH.read_text(encoding="utf-8"))
            if isinstance(do_arquivo, dict):
                cenarios.update(do_arquivo)
    except (json.JSONDecodeError, OSError):
        # Cenários quebrados não devem derrubar o sistema — usamos só os padrão.
        pass
    return cenarios


def cenarios_disponiveis():
    """Lista os nomes de cenários disponíveis para teste."""
    return sorted(_carregar_cenarios().keys())


def _amostrar(valor):
    """Resolve o valor de um override de cenário."""
    if isinstance(valor, (list, tuple)) and len(valor) == 2:
        lo, hi = valor
        if isinstance(lo, int) and isinstance(hi, int):
            return random.randint(lo, hi)
        return round(random.uniform(float(lo), float(hi)), 2)
    return valor


def _resolver_overrides(cenario):
    """Converte o argumento `cenario` num dicionário de overrides {param: valor}."""
    if cenario is None:
        return {}
    if isinstance(cenario, dict):  # overrides diretos
        return cenario
    cenarios = _carregar_cenarios()
    return cenarios.get(str(cenario), {})  # nome desconhecido => nominal


def coletar(cenario="nominal"):
    """Coleta UMA leitura de telemetria do satélite.

    Args:
        cenario: nome de um cenário ('nominal', 'sobreaquecimento_transponder',
                 ...), OU um dict de overrides {param: valor}, OU None.

    Returns:
        dict com todos os parâmetros + metadados (timestamp, satelite, cenario).
    """
    leitura = {}
    for param, info in FAIXAS_NOMINAIS.items():
        lo, hi = info["faixa"]
        if isinstance(lo, int) and isinstance(hi, int):
            leitura[param] = random.randint(lo, hi)
        else:
            leitura[param] = round(random.uniform(lo, hi), 2)

    # Aplica o cenário por cima das leituras nominais.
    for param, valor in _resolver_overrides(cenario).items():
        leitura[param] = _amostrar(valor)

    leitura["_satelite"] = SATELITE
    leitura["_cenario"] = cenario if isinstance(cenario, str) else "custom"
    leitura["_timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return leitura


def simular_orbita(n_ciclos=6, cenario="nominal"):
    """Gera uma série temporal de `n_ciclos` leituras — útil para visualizar a
    evolução ao longo de ciclos orbitais (eclipse, aquecimento etc.).

    Retorna uma lista de leituras (cada uma como em `coletar`)."""
    serie = []
    for _ in range(max(1, n_ciclos)):
        serie.append(coletar(cenario))
    return serie


def metadados(leitura):
    """Extrai os metadados ( _satelite / _cenario / _timestamp ) de uma leitura."""
    return {
        "satelite": leitura.get("_satelite", SATELITE),
        "cenario": leitura.get("_cenario", "nominal"),
        "timestamp": leitura.get("_timestamp", ""),
    }


def parametros(leitura):
    """Retorna apenas os parâmetros de telemetria (sem as chaves de metadados)."""
    return {k: v for k, v in leitura.items() if not k.startswith("_")}


if __name__ == "__main__":
    # Execução direta: imprime um exemplo de cada cenário (debug rápido).
    import pprint
    for nome in cenarios_disponiveis():
        print(f"\n=== Cenário: {nome} ===")
        pprint.pp(coletar(nome))
