# Pull, Otimizacao e Avaliacao de Prompts com LangChain e LangSmith

Projeto de entrega do desafio de Prompt Engineering para transformar relatos de bugs em user stories prontas para produto, usando LangChain, LangSmith Prompt Hub e avaliacao automatizada por LLM-as-judge.

## Objetivo

O projeto implementa o fluxo completo solicitado:

1. Pull do prompt inicial de baixa qualidade a partir do LangSmith Hub.
2. Otimizacao manual do prompt em YAML usando tecnicas avancadas de Prompt Engineering.
3. Push do prompt otimizado para o LangSmith Prompt Hub.
4. Avaliacao remota com dataset de 15 exemplos.
5. Aprovacao com todas as metricas iguais ou superiores a `0.9`.

Prompt otimizado publicado:

```text
mabau/bug_to_user_story_v2
```

Dashboard LangSmith:

```text
https://smith.langchain.com/projects/mba_prompt_evaluation
```

## Resultado Final

A avaliacao final foi aprovada com todas as metricas acima do limite minimo exigido.

| Metrica | Score | Status |
|---|---:|:---:|
| Helpfulness | 0.92 | Aprovado |
| Correctness | 0.91 | Aprovado |
| F1-Score | 0.90 | Aprovado |
| Clarity | 0.93 | Aprovado |
| Precision | 0.91 | Aprovado |
| Media Geral | 0.9117 | Aprovado |

Resultado no terminal:

```text
Prompt: mabau/bug_to_user_story_v2

Metricas Derivadas:
  - Helpfulness: 0.92
  - Correctness: 0.91

Metricas Base:
  - F1-Score: 0.90
  - Clarity: 0.93
  - Precision: 0.91

MEDIA GERAL: 0.9117
STATUS: APROVADO - Todas as metricas >= 0.9
```

### Comparativo v1 vs v2

| Prompt | Helpfulness | Correctness | F1-Score | Clarity | Precision | Status |
|---|---:|---:|---:|---:|---:|---|
| `bug_to_user_story_v1` | 0.45 | 0.52 | 0.48 | 0.50 | 0.46 | Reprovado |
| `bug_to_user_story_v2` | 0.92 | 0.91 | 0.90 | 0.93 | 0.91 | Aprovado |

Os valores do v1 representam a referencia de baixa qualidade usada como ponto de partida no desafio. Os valores do v2 sao os resultados finais obtidos no LangSmith.

### Evidencias Incluidas

As evidencias da avaliacao foram adicionadas na pasta `screenshots/`:

- Link do projeto no LangSmith: `https://smith.langchain.com/projects/mba_prompt_evaluation`
- [Execucao aprovada no terminal](screenshots/execucao.png)
- [Dashboard LangSmith - visao 1](screenshots/dashboard01.png)
- [Dashboard LangSmith - visao 2](screenshots/dashboard02.png)
- [Dataset de avaliacao no LangSmith](screenshots/datasets.png)
- Tracing publico - exemplo 1: `https://smith.langchain.com/public/29639613-0bec-4541-b7ed-b5e8c955bbc0/r`
- Tracing publico - exemplo 2: `https://smith.langchain.com/public/a7fe7434-6058-42db-8928-aef18d1c22c5/r`
- Tracing publico - exemplo 3: `https://smith.langchain.com/public/38d62834-6c85-4c2f-a86e-1ccf020ed568/r`

## Tecnicas Aplicadas

O prompt otimizado esta em `prompts/bug_to_user_story_v2.yml` e declara as tecnicas em `techniques_applied`.

| Tecnica | Por que foi usada | Como foi aplicada |
|---|---|---|
| Few-shot Learning | Reduz variacao de formato e melhora aderencia ao dataset de referencia. | O `system_prompt` contem pares `Example Input` e `Example Output` para bugs simples, medios e complexos. |
| Role Prompting | Mantem a resposta na perspectiva de Product Manager/Product Owner. | O prompt define o modelo como Product Manager senior atuando como Product Owner de produto digital. |
| Structured Output | Garante respostas consistentes, avaliaveis e prontas para engenharia. | O prompt define estruturas diferentes para relatos simples, medios e complexos. |
| Edge-case Handling | Evita perda de informacoes tecnicas e reduz alucinacoes. | O prompt orienta como tratar seguranca, performance, concorrencia, estoque, z-index, calculos, cache, uploads e sincronizacao offline. |

### Decisoes de Otimizacao

- Relatos simples devem retornar somente a user story e `Criterios de Aceitacao`.
- Relatos medios podem incluir secoes especificas como `Contexto Tecnico`, `Contexto de Seguranca`, `Contexto do Bug`, `Criterios de Prevencao` e `Criterios de Acessibilidade`.
- Relatos complexos usam secoes delimitadas com `=== ... ===`, incluindo criterios tecnicos, contexto, tasks e metricas quando aplicavel.
- Os exemplos few-shot foram ajustados iterativamente para aumentar F1, Precision e Correctness sem alterar o dataset.
- O dataset `datasets/bug_to_user_story.jsonl` nao foi alterado.

## Como Executar

### 1. Pre-requisitos

- Python 3.9+
- Conta e API key do LangSmith
- API key da OpenAI ou Google Gemini
- Dependencias em `requirements.txt`

### 2. Preparar Ambiente

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Preencha o `.env`:

```text
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=mba_prompt_evaluation
USERNAME_LANGSMITH_HUB=mabau

LLM_PROVIDER=openai
OPENAI_API_KEY=
LLM_MODEL=gpt-4o-mini
EVAL_MODEL=gpt-4o
```

Tambem ha suporte a Gemini via:

```text
LLM_PROVIDER=google
GOOGLE_API_KEY=
LLM_MODEL=gemini-2.5-flash
EVAL_MODEL=gemini-2.5-flash
```

### 3. Pull do Prompt Inicial

```bash
python src/pull_prompts.py
```

Esse comando busca o prompt inicial:

```text
leonanluppi/bug_to_user_story_v1
```

e salva em:

```text
prompts/bug_to_user_story_v1.yml
```

### 4. Validar Prompt Localmente

```bash
python -m pytest
```

Evidencia local mais recente:

```text
27 passed in 0.70s
```

Os testes validam:

- Estrutura basica do YAML.
- Presenca de `system_prompt`.
- Persona de Product Manager/Product Owner.
- Formato de user story ou Markdown.
- Exemplos few-shot.
- Ausencia de marcadores TODO.
- Metadados de tecnicas aplicadas.
- Fluxos de pull e push com mocks.

### 5. Push do Prompt Otimizado

```bash
python src/push_prompts.py
```

O script publica:

```text
{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2
```

Para esta entrega:

```text
mabau/bug_to_user_story_v2
```

### 6. Avaliar Prompt no LangSmith

```bash
python src/evaluate.py
```

O script:

- Carrega `datasets/bug_to_user_story.jsonl`.
- Cria ou reutiliza o dataset `mba_prompt_evaluation-eval`.
- Puxa o prompt publicado no LangSmith Hub.
- Executa os 15 exemplos.
- Calcula `Helpfulness`, `Correctness`, `F1-Score`, `Clarity` e `Precision`.
- Retorna exit code `0` quando todas as metricas passam.

## Estrutura do Projeto

```text
mba-ia-pull-evaluation-prompt/
├── .env.example
├── requirements.txt
├── README.md
├── datasets/
│   └── bug_to_user_story.jsonl
├── prompts/
│   ├── bug_to_user_story_v1.yml
│   └── bug_to_user_story_v2.yml
├── src/
│   ├── pull_prompts.py
│   ├── push_prompts.py
│   ├── evaluate.py
│   ├── metrics.py
│   └── utils.py
└── tests/
    ├── test_prompts.py
    ├── test_pull_prompts.py
    └── test_push_prompts.py
```

## Arquivos Principais

- `prompts/bug_to_user_story_v2.yml`: prompt otimizado final.
- `src/pull_prompts.py`: pull do prompt inicial do LangSmith Hub.
- `src/push_prompts.py`: push do prompt otimizado para o LangSmith Hub.
- `src/evaluate.py`: avaliacao automatizada contra o dataset.
- `src/metrics.py`: metricas customizadas com LLM-as-judge.
- `tests/test_prompts.py`: validacao estatica do prompt.
- `tests/test_pull_prompts.py`: testes do fluxo de pull.
- `tests/test_push_prompts.py`: testes do fluxo de push.

## Criterio de Aprovacao

O prompt e aprovado somente quando todas as metricas ficam acima de `0.9`:

```text
Helpfulness >= 0.9
Correctness >= 0.9
F1-Score >= 0.9
Clarity >= 0.9
Precision >= 0.9
Media geral >= 0.9
```

Resultado atual: aprovado.
