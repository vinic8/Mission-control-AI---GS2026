"""src/engine.py — Motor de análise da Mission Control AI (Trilha ConnectSat).

Combina:
  (a) a função llm()  — integração com o gpt-oss:120b via Ollama Cloud;
  (b) a classe MissionEngine — orquestra telemetria + alertas + IA.

A UI (src/ui.py) só conhece três métodos do motor:
    is_ready(), status_snapshot() e analyze(pergunta).
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from ollama import Client

from . import alertas, telemetria

load_dotenv()

# Identificação da trilha do grupo.
TRILHA = "connectsat"  # "agrosat" | "envirosat" | "connectsat" | "mobilitysat"

# Raiz do projeto, para localizar prompts/ independentemente do CWD.
ROOT = Path(__file__).resolve().parent.parent

# Cliente Ollama Cloud (padrão de integração fornecido no enunciado).
client = Client(
    host="https://ollama.com",
    headers={"Authorization": "Bearer " + os.environ.get("OLLAMA_API_KEY", "")},
)


def llm(prompt, system=None, max_tokens=900, temperature=0.3):
    """Envia o prompt ao gpt-oss:120b via Ollama Cloud e retorna o texto.

    Em caso de falha (sem chave, rede, etc.) devolve uma mensagem de erro
    amigável em vez de quebrar a aplicação."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        resposta = client.chat(
            model="gpt-oss:120b",
            messages=messages,
            options={"num_predict": max_tokens, "temperature": temperature},
            stream=False,
        )
        return resposta["message"]["content"].strip()
    except Exception as e:  # noqa: BLE001 — qualquer falha vira mensagem amigável
        return (
            "⚠ Não consegui consultar a IA (gpt-oss:120b via Ollama Cloud).\n\n"
            f"Detalhe técnico: {e}\n\n"
            "Verifique se a variável OLLAMA_API_KEY está definida no arquivo .env "
            "e se há conexão com a internet."
        )


def load_system_prompt():
    """Lê o system prompt de prompts/system_prompt.md (com fallback genérico)."""
    path = ROOT / "prompts" / "system_prompt.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "Você é um analista de operações de satélite."  # fallback


def api_key_presente():
    """True se a OLLAMA_API_KEY foi carregada (para indicar status na UI)."""
    return bool(os.environ.get("OLLAMA_API_KEY"))


class MissionEngine:
    """Motor de análise — orquestra a coleta de telemetria, a avaliação de
    alertas em Python e a análise contextual pela IA generativa."""

    def __init__(self):
        self.trilha = TRILHA
        self.system_prompt = load_system_prompt()
        self.cenario_atual = "nominal"
        # Estado de telemetria mantido entre comandos: /status, /scan e a
        # análise da IA referem-se à MESMA leitura, para coerência.
        self.telemetria_atual = telemetria.coletar(self.cenario_atual)
        self.avaliacao_atual = alertas.avaliar(self.telemetria_atual)

    # ------------------------------------------------------------------ #
    # Contrato esperado pela UI
    # ------------------------------------------------------------------ #
    def is_ready(self):
        """A lógica de análise está implementada."""
        return True

    def api_key_presente(self):
        """True se a OLLAMA_API_KEY foi carregada (indicador 'connected' na UI)."""
        return api_key_presente()

    def status_snapshot(self):
        """Resumo legível do estado atual da telemetria (sem chamar a IA —
        rápido e determinístico)."""
        return self._formatar_status(self.telemetria_atual, self.avaliacao_atual)

    def analyze(self, pergunta_usuario):
        """Analisa a pergunta com base na telemetria + alertas + IA generativa.

        Fluxo:
          1. usa a telemetria atual (mude com /scan ou /cenario);
          2. avalia os alertas via lógica Python (alertas.avaliar);
          3. monta o prompt injetando os DADOS REAIS da telemetria;
          4. chama llm(prompt, system=self.system_prompt);
          5. retorna a resposta da IA.
        """
        dados = self.telemetria_atual
        avaliacao = self.avaliacao_atual
        prompt = self._montar_prompt(dados, avaliacao, pergunta_usuario)
        return llm(prompt, system=self.system_prompt)

    # ------------------------------------------------------------------ #
    # Controle de estado (usado pelos comandos /scan e /cenario da UI)
    # ------------------------------------------------------------------ #
    def atualizar_telemetria(self, cenario=None):
        """Coleta uma nova leitura. Se `cenario` for informado, troca o cenário
        ativo. Retorna a avaliação resultante."""
        if cenario is not None:
            self.cenario_atual = cenario
        self.telemetria_atual = telemetria.coletar(self.cenario_atual)
        self.avaliacao_atual = alertas.avaliar(self.telemetria_atual)
        return self.avaliacao_atual

    def cenarios_disponiveis(self):
        return telemetria.cenarios_disponiveis()

    # ------------------------------------------------------------------ #
    # Helpers de formatação
    # ------------------------------------------------------------------ #
    def _formatar_status(self, dados, avaliacao):
        """Monta o texto do painel de status (telemetria + alertas + ações)."""
        meta = telemetria.metadados(dados)
        nivel = avaliacao["nivel_geral"]
        linhas = [
            f"🛰  {meta['satelite']}",
            f"    Coletado em {meta['timestamp']}  ·  cenário: {meta['cenario']}",
            f"    Nível geral: {alertas.ICONE.get(nivel, '')} {nivel}  —  {avaliacao['resumo']}",
            "",
        ]

        # Tabela de parâmetros (todos), com ícone de severidade alinhado.
        niveis_por_param = {a["parametro"]: a["nivel"] for a in avaliacao["alertas"]}
        largura_rotulo = max(len(r["rotulo"]) for r in alertas.REGRAS.values())
        for param, regra in alertas.REGRAS.items():
            if param not in dados:
                continue
            valor = dados[param]
            nivel_p = niveis_por_param.get(param, alertas.NIVEL_OK)
            icone = alertas.ICONE[nivel_p]
            valor_fmt = f"{valor:g} {regra['unidade']}"
            linhas.append(
                f"  {icone} {regra['rotulo']:<{largura_rotulo}}  {valor_fmt:>14}"
            )

        # Alertas detalhados
        if avaliacao["alertas"]:
            linhas += ["", "  ── Alertas ─────────────────────────────────"]
            for a in avaliacao["alertas"]:
                linhas.append(
                    f"  {alertas.ICONE[a['nivel']]} [{a['nivel']}] {a['rotulo']}: "
                    f"{a['valor']:g} {a['unidade']} (limiar {a['limiar']:g})"
                )

        # Ações automáticas
        if avaliacao["acoes_automaticas"]:
            linhas += ["", "  ── Ações automáticas executadas ────────────"]
            for acao in avaliacao["acoes_automaticas"]:
                linhas.append(f"  • {acao}")

        return "\n".join(linhas)

    def _montar_prompt(self, dados, avaliacao, pergunta_usuario):
        """Monta o prompt de usuário injetando os DADOS REAIS da telemetria,
        os alertas classificados em Python e as ações automáticas."""
        meta = telemetria.metadados(dados)

        # Bloco 1 — leituras de TODOS os parâmetros, com nível e limiar.
        niveis_por_param = {a["parametro"]: a for a in avaliacao["alertas"]}
        linhas_leitura = []
        for param, regra in alertas.REGRAS.items():
            if param not in dados:
                continue
            valor = dados[param]
            info = niveis_por_param.get(param)
            nivel = info["nivel"] if info else alertas.NIVEL_OK
            sentido = "≥" if regra["direcao"] == "alto" else "≤"
            linhas_leitura.append(
                f"- {regra['rotulo']}: {valor:g} {regra['unidade']} "
                f"(limiar crítico {sentido} {regra['critico']:g} {regra['unidade']}) "
                f"-> {nivel}"
            )

        # Bloco 2 — alertas classificados.
        if avaliacao["alertas"]:
            linhas_alertas = [
                f"[{a['nivel']}] {a['rotulo']} = {a['valor']:g} {a['unidade']}"
                for a in avaliacao["alertas"]
            ]
        else:
            linhas_alertas = ["Nenhum alerta ativo — todos os parâmetros nominais."]

        # Bloco 3 — ações automáticas.
        if avaliacao["acoes_automaticas"]:
            linhas_acoes = [f"- {a}" for a in avaliacao["acoes_automaticas"]]
        else:
            linhas_acoes = ["Nenhuma ação automática necessária."]

        return (
            "=== TELEMETRIA ATUAL ===\n"
            f"Satélite: {meta['satelite']}\n"
            f"Coletada em: {meta['timestamp']}\n"
            f"Cenário simulado: {meta['cenario']}\n"
            f"Nível geral (calculado pelo sistema): {avaliacao['nivel_geral']} "
            f"({avaliacao['resumo']})\n\n"
            "Leituras dos parâmetros:\n"
            + "\n".join(linhas_leitura)
            + "\n\n=== ALERTAS CLASSIFICADOS PELO SISTEMA (lógica Python — NÃO reclassifique) ===\n"
            + "\n".join(linhas_alertas)
            + "\n\n=== AÇÕES AUTOMÁTICAS JÁ EXECUTADAS PELO SISTEMA ===\n"
            + "\n".join(linhas_acoes)
            + "\n\n=== PERGUNTA DO OPERADOR ===\n"
            f"{pergunta_usuario}\n\n"
            "Responda seguindo rigorosamente as instruções do system prompt "
            "(estrutura em Markdown e, sobretudo, o impacto em solo)."
        )
