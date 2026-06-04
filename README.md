# 🚀 Mission Control AI — ConnectSat

Sistema de monitoramento operacional de um satélite de telecomunicações em órbita baixa (LEO) voltado à **conectividade rural e inclusão digital**. Recebe telemetria simulada, detecta anomalias por lógica Python e usa IA generativa (gpt-oss:120b via Ollama Cloud) para analisar o estado da missão em linguagem natural — sempre amarrando cada anomalia ao seu **impacto em solo**.

---

## 👥 Integrantes
- Nome Completo — RM: XXXXXX — Turma: XXXXX
- Nome Completo — RM: XXXXXX — Turma: XXXXX
- Nome Completo — RM: XXXXXX — Turma: XXXXX
- Nome Completo — RM: XXXXXX — Turma: XXXXX

> Preencha com os dados reais do grupo antes de entregar.

---

## 🛰 O que o projeto faz
A Mission Control AI monitora a telemetria de um satélite de telecom LEO (estilo Starlink/OneWeb) e classifica o estado da missão em **🟢 OK / 🟡 ATENÇÃO / 🔴 CRÍTICO** usando **regras de threshold em Python** (`src/alertas.py`). Diante de condições críticas, o sistema dispara **respostas automáticas** (modo seguro térmico, economia de energia, failover de antena, recalibração de apontamento, balanceamento de carga, modulação adaptativa).

A **IA generativa** (gpt-oss:120b) recebe os dados reais da telemetria injetados no prompt e produz uma análise contextual: situação geral, análise técnica, **impacto em solo** (escolas, postos de saúde, negócios rurais) e recomendações. A IA **explica**; o código **decide** a severidade.

---

## 🎯 Persona atendida
**Engenheiro(a) de NOC da operadora** (persona principal), com o sistema também falando a linguagem do **coordenador de inclusão digital** e do **cliente final em comunidade rural**. Justificativa: o NOC precisa de diagnóstico técnico e priorização imediatos; o diferencial do projeto é traduzir esse diagnóstico no impacto humano de cada anomalia, atendendo também quem não é técnico.

---

## 🧰 Tecnologias utilizadas
- Python 3.10+
- Ollama Cloud API (modelo **gpt-oss:120b**)
- Bibliotecas: `ollama`, `python-dotenv`, `rich`, `prompt-toolkit`, `pyfiglet`

---

## ▶️ Como executar
1. Clone o repositório.
2. Crie o ambiente virtual:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   # Windows: python -m venv .venv && .venv\Scripts\activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Crie o arquivo `.env` na raiz (copie de `.env.example`) com a sua chave:
   ```
   OLLAMA_API_KEY=sua_chave_aqui_sem_aspas
   ```
5. Execute:
   ```bash
   python main.py
   ```

### Comandos da CLI
| Comando | O que faz |
| --- | --- |
| `/help` | Lista os comandos |
| `/status` | Telemetria atual + alertas + ações automáticas |
| `/scan` | Coleta uma nova leitura no cenário atual |
| `/cenario <nome>` | Troca o cenário simulado (ex.: `/cenario bateria_critica`) |
| `/cenarios` | Lista os cenários disponíveis |
| `/about` | Sobre o projeto |
| `/clear` | Limpa a tela |
| `/exit` | Encerra |
| `<pergunta>` | Vai para a análise da IA (ex.: *"Como está a missão?"*) |

---

## 🖼 Demonstração
![Banner inicial da missão](assets/screenshot_banner.png)
![Alerta crítico com análise da IA](assets/screenshot_analise.png)

> Capture os dois prints com o sistema rodando (instruções em `assets/LEIA-ME.txt`).

---

## 🧠 System Prompt
O system prompt completo está em [`prompts/system_prompt.md`](prompts/system_prompt.md). Ele define **papel** (analista de NOC da ConnectSat), **escopo** (apenas o estado da missão), **restrições** (usar só os dados fornecidos, não reclassificar a severidade decidida em Python, sempre conectar com a Terra), **tom** (sala de controle) e **formato de saída** (Markdown estruturado com a seção obrigatória *🌎 Impacto em solo*).

### Decisões de design do prompt (iterações)
- **v1 — genérico demais.** *"Você é um assistente que analisa dados de satélite."* Resultado: a IA respondia qualquer coisa e raramente citava o impacto terrestre. Sem papel nem restrições, não condicionava nada.
- **v2 — rígido demais.** Passamos a exigir um template fixo de seções. Resultado: a IA repetia todas as seções mesmo para perguntas pontuais (ex.: *"qual a latência?"*), ficando verbosa e robótica.
- **v3 (atual) — papel + escopo + restrições + tom + formato, com flexibilidade.** Definimos a missão (conectividade rural), as personas, a regra "a IA explica, o código decide", e tornamos as seções **omissíveis** quando não se aplicam. Adicionamos um exemplo de raciocínio para fixar o estilo. Resultado: respostas estáveis, técnicas e que sempre amarram o impacto em solo.

> Recomendação: rode o mesmo cenário 3+ vezes com `temperature=0.3` e observe a consistência.

---

## 🧪 Cenários de teste demonstrados
1. **Operação normal** (`/cenario nominal`) — todos os parâmetros dentro da faixa; nível 🟢 OK.
2. **Temperatura crítica** (`/cenario sobreaquecimento_transponder`) — transponder acima de 78 °C; dispara modo seguro térmico + análise da IA.
3. **Bateria crítica em eclipse** (`/cenario bateria_critica`) — aciona modo economia de energia; impacto: comunidades offline até recarregar.
4. **Perda de apontamento** (`/cenario perda_apontamento`) — erro de beam steering crítico; recalibração automática.
5. **Degradação da antena** (`/cenario degradacao_antena`) — failover para feixe redundante.
6. **Congestionamento do feixe** (`/cenario congestionamento`) — latência alta e SNR baixa; balanceamento de carga.
7. **Caso extremo — blackout total** (`/cenario blackout_total`) — múltiplas falhas simultâneas; teste de robustez.

---

## ⚠️ Limitações conhecidas
- A telemetria é **simulada** (aleatória dentro de faixas plausíveis), não vem de um satélite real.
- A IA analisa um **instantâneo** de telemetria, não uma série contínua: não há causa-raiz confirmada nem previsão temporal real.
- As respostas da IA são **não-determinísticas**; mesmo com `temperature=0.3` pode haver variação de redação entre execuções.
- As "ações automáticas" são **simuladas** (mensagens), não enviam comandos reais ao satélite.
- Requer **chave válida do Ollama Cloud** e internet; sem isso, a CLI sobe normalmente mas a análise retorna uma mensagem de erro amigável (a lógica de alertas/`/status` continua funcionando offline).
- A `usuarios_conectados` baixa é tratada como **indicador de impacto**, não necessariamente como causa-raiz.

---

## 🎥 Vídeo de demonstração
🎥 [Assistir no YouTube](https://www.youtube.com/watch?v=COLE_O_LINK_AQUI)
