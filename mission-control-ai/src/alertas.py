"""src/alertas.py — Thresholds, regras de decisão e respostas automáticas.

REGRA DE OURO DO PROJETO:
    Toda a decisão "isto é crítico ou não" vive AQUI, em Python determinístico.
    A IA (system_prompt) apenas EXPLICA e CONTEXTUALIZA o que o código já
    classificou — ela nunca decide a severidade.

Cada parâmetro carrega, além dos limiares, o seu IMPACTO TERRESTRE: o que aquela
anomalia significa para escolas rurais, postos de saúde / telemedicina e
pequenos negócios atendidos pelo feixe. Esse é o diferencial "conectar com a
Terra".
"""

# Níveis de severidade
NIVEL_OK = "OK"
NIVEL_ATENCAO = "ATENÇÃO"
NIVEL_CRITICO = "CRÍTICO"

# Ícones por nível (seguros para exibir como texto puro)
ICONE = {NIVEL_OK: "🟢", NIVEL_ATENCAO: "🟡", NIVEL_CRITICO: "🔴"}

# Ordem de gravidade (para calcular o pior nível geral)
_GRAVIDADE = {NIVEL_OK: 0, NIVEL_ATENCAO: 1, NIVEL_CRITICO: 2}

# ---------------------------------------------------------------------------
# REGRAS DE THRESHOLD
#   direcao = "alto"  -> valores ALTOS são ruins  (latência, temperatura, erro)
#   direcao = "baixo" -> valores BAIXOS são ruins (throughput, bateria, SNR…)
# Os campos `atencao` e `critico` são os limiares de cada faixa.
# ---------------------------------------------------------------------------
REGRAS = {
    "latencia_uplink_ms": {
        "rotulo": "Latência de uplink",
        "unidade": "ms",
        "direcao": "alto",
        "atencao": 60.0,
        "critico": 100.0,
        "impacto": ("Latência alta trava videochamadas de telemedicina e aulas "
                    "ao vivo: a teleconsulta fica com atraso e o aluno perde a "
                    "sincronia com o professor."),
    },
    "throughput_feixe_mbps": {
        "rotulo": "Throughput do feixe",
        "unidade": "Mbps",
        "direcao": "baixo",
        "atencao": 150.0,
        "critico": 100.0,
        "impacto": ("Queda de banda no feixe reduz a velocidade nas escolas e "
                    "UBS atendidas: plataformas de ensino e envio de exames "
                    "ficam lentos ou inacessíveis."),
    },
    "saude_antena_pct": {
        "rotulo": "Saúde da antena phased-array",
        "unidade": "%",
        "direcao": "baixo",
        "atencao": 85.0,
        "critico": 70.0,
        "impacto": ("Degradação da antena encolhe a área de cobertura: "
                    "comunidades na borda do feixe começam a ficar sem sinal."),
    },
    "erro_beam_steering_deg": {
        "rotulo": "Erro de beam steering",
        "unidade": "°",
        "direcao": "alto",
        "atencao": 0.30,
        "critico": 0.60,
        "impacto": ("Erro de apontamento desloca o feixe do alvo geográfico: a "
                    "célula rural servida pode sair da cobertura e perder a "
                    "conexão por completo."),
    },
    "temp_transponder_c": {
        "rotulo": "Carga térmica do transponder",
        "unidade": "°C",
        "direcao": "alto",
        "atencao": 65.0,
        "critico": 78.0,
        "impacto": ("Sobreaquecimento força a redução de potência do "
                    "transponder: menos capacidade para a região e risco de "
                    "queda total do serviço se não estabilizar."),
    },
    "bateria_pct": {
        "rotulo": "Bateria",
        "unidade": "%",
        "direcao": "baixo",
        "atencao": 40.0,
        "critico": 20.0,
        "impacto": ("Bateria baixa em eclipse orbital ameaça a continuidade: "
                    "feixes secundários podem ser desligados, deixando "
                    "comunidades inteiras offline até o satélite recarregar."),
    },
    "snr_db": {
        "rotulo": "Relação sinal-ruído (SNR)",
        "unidade": "dB",
        "direcao": "baixo",
        "atencao": 10.0,
        "critico": 6.0,
        "impacto": ("SNR baixa aumenta erros e retransmissões: a conexão fica "
                    "instável para todos no feixe, com quedas intermitentes."),
    },
    "usuarios_conectados": {
        "rotulo": "Usuários conectados",
        "unidade": "usuários",
        "direcao": "baixo",
        "atencao": 1000,
        "critico": 200,
        "impacto": ("O número de usuários conectados despencou — sinal de "
                    "interrupção afetando escolas, UBS e negócios que dependem "
                    "exclusivamente deste enlace."),
    },
}


def _classificar(valor, regra):
    """Classifica UM parâmetro em OK / ATENÇÃO / CRÍTICO segundo seus limiares."""
    if regra["direcao"] == "alto":
        if valor >= regra["critico"]:
            return NIVEL_CRITICO
        if valor >= regra["atencao"]:
            return NIVEL_ATENCAO
        return NIVEL_OK
    else:  # direcao == "baixo"
        if valor <= regra["critico"]:
            return NIVEL_CRITICO
        if valor <= regra["atencao"]:
            return NIVEL_ATENCAO
        return NIVEL_OK


def classificar_parametro(param, valor):
    """Classifica um parâmetro avulso. Retorna NIVEL_OK se não houver regra."""
    regra = REGRAS.get(param)
    if regra is None:
        return NIVEL_OK
    return _classificar(valor, regra)


def respostas_automaticas(dados):
    """RESPOSTAS AUTOMATIZADAS a situações críticas — decididas em Python.

    Cada `if` representa uma ação que o satélite/NOC executaria sozinho diante
    de uma condição crítica. Retorna a lista de ações acionadas."""
    acoes = []

    # 1. Proteção térmica do transponder
    if dados.get("temp_transponder_c", 0) >= REGRAS["temp_transponder_c"]["critico"]:
        acoes.append("🔥 MODO SEGURO TÉRMICO ativado: potência do transponder "
                     "reduzida em 30% para proteger o hardware.")

    # 2. Economia de energia (bateria crítica em eclipse)
    if dados.get("bateria_pct", 100) <= REGRAS["bateria_pct"]["critico"]:
        acoes.append("🔋 MODO ECONOMIA DE ENERGIA ativado: feixes secundários "
                     "desligados; prioridade para enlaces essenciais (UBS e escolas).")

    # 3. Recalibração de apontamento
    if dados.get("erro_beam_steering_deg", 0) >= REGRAS["erro_beam_steering_deg"]["critico"]:
        acoes.append("🎯 RECALIBRAÇÃO DE APONTAMENTO iniciada: realinhando o "
                     "phased-array ao centro da célula-alvo.")

    # 4. Failover de antena
    if dados.get("saude_antena_pct", 100) <= REGRAS["saude_antena_pct"]["critico"]:
        acoes.append("📡 FAILOVER acionado: tráfego roteado para antena/feixe "
                     "redundante.")

    # 5. Balanceamento de carga (congestionamento / latência ou throughput crítico)
    lat_critica = dados.get("latencia_uplink_ms", 0) >= REGRAS["latencia_uplink_ms"]["critico"]
    thr_critico = dados.get("throughput_feixe_mbps", 9e9) <= REGRAS["throughput_feixe_mbps"]["critico"]
    if lat_critica or thr_critico:
        acoes.append("🔀 BALANCEAMENTO DE CARGA: redistribuindo usuários para "
                     "satélites vizinhos da constelação.")

    # 6. Modulação adaptativa (SNR crítico)
    if dados.get("snr_db", 99) <= REGRAS["snr_db"]["critico"]:
        acoes.append("🛡 MODULAÇÃO ADAPTATIVA: reduzindo a ordem de modulação "
                     "(ex.: 16QAM → QPSK) para preservar o enlace.")

    return acoes


def _pior_nivel(alertas):
    """Retorna o pior nível presente na lista de alertas."""
    pior = NIVEL_OK
    for a in alertas:
        if _GRAVIDADE[a["nivel"]] > _GRAVIDADE[pior]:
            pior = a["nivel"]
    return pior


def _resumo(alertas):
    """Texto curto: 'X crítico(s), Y atenção'."""
    n_crit = sum(1 for a in alertas if a["nivel"] == NIVEL_CRITICO)
    n_aten = sum(1 for a in alertas if a["nivel"] == NIVEL_ATENCAO)
    if n_crit == 0 and n_aten == 0:
        return "Todos os parâmetros nominais."
    partes = []
    if n_crit:
        partes.append(f"{n_crit} crítico(s)")
    if n_aten:
        partes.append(f"{n_aten} em atenção")
    return ", ".join(partes) + "."


def avaliar(dados):
    """Avalia uma leitura de telemetria e devolve um diagnóstico estruturado.

    Returns dict:
        {
          "alertas": [ {parametro, rotulo, valor, unidade, nivel, limiar,
                        impacto_terrestre}, ... ],   # só ATENÇÃO/CRÍTICO
          "acoes_automaticas": [str, ...],
          "nivel_geral": "OK" | "ATENÇÃO" | "CRÍTICO",
          "resumo": "2 crítico(s), 1 em atenção.",
        }
    """
    alertas = []
    for param, regra in REGRAS.items():
        if param not in dados:
            continue
        valor = dados[param]
        nivel = _classificar(valor, regra)
        if nivel == NIVEL_OK:
            continue
        limiar = regra["critico"] if nivel == NIVEL_CRITICO else regra["atencao"]
        alertas.append({
            "parametro": param,
            "rotulo": regra["rotulo"],
            "valor": valor,
            "unidade": regra["unidade"],
            "nivel": nivel,
            "limiar": limiar,
            "impacto_terrestre": regra["impacto"],
        })

    return {
        "alertas": alertas,
        "acoes_automaticas": respostas_automaticas(dados),
        "nivel_geral": _pior_nivel(alertas),
        "resumo": _resumo(alertas),
    }


if __name__ == "__main__":
    # Debug rápido: avalia um cenário de exemplo.
    from telemetria import coletar  # type: ignore
    import pprint
    for nome in ["nominal", "sobreaquecimento_transponder", "blackout_total"]:
        print(f"\n=== {nome} ===")
        pprint.pp(avaliar(coletar(nome)))
