# MuTAP Demo — Geração de Testes com LLMs e Teste de Mutação

Implementação didática do pipeline **MuTAP (Mutation Test case generation using Augmented Prompt)**, proposto no artigo *["Effective Test Generation Using Pre-trained Large Language Models and Mutation Testing"](https://arxiv.org/abs/2308.16557) (arXiv:2308.16557)* (Dakhel et al., 2023).

## Objetivo

Demonstrar como **Large Language Models (LLMs)** podem gerar testes unitários automatizados e como o **Teste de Mutação** pode ser usado como mecanismo de feedback para melhorar iterativamente a eficácia desses testes na detecção de bugs.

O projeto implementa o pipeline completo do MuTAP, incluindo todas as etapas do artigo original:

1. **Geração inicial** — LLM gera um teste inicial para a PUT (zero-shot ou few-shot)
2. **Correção sintática** — Teste é executado; se falhar, LLM corrige erros de sintaxe
3. **Correção semântica** — Cada `assert` é executado individualmente contra a PUT; valores esperados errados são corrigidos automaticamente computando o valor real
4. **Mutação** — MutPy cria mutantes (versões com bugs sintéticos) da função
5. **Mutation Score** — Testes são executados contra os mutantes → MS inicial
6. **Prompt aumentado** — Mutantes sobreviventes viram contexto para o LLM gerar novos testes direcionados
7. **Loop** — Repete até MS = 100% ou limite de iterações
8. **Minimização greedy** — Remove asserções redundantes mantendo o MS máximo

![fluxo-de-mutacao](./assets/mutation.png)
![diagrama-mutap](./assets/diagrama-mutap.png)

## Stack

| Camada | Tecnologia | Função |
|---|---|---|
| **LLM** | **Gemini API** (padrão) | Geração de testes via API Google (gratuito, 60 req/min) |
| | **Ollama + CodeLlama** (alternativa) | LLM local, sem dependência externa |
| **Mutação** | **MutPy** | Gera mutantes (bugs sintéticos) do código testado |
| **Testes** | **Pytest** | Executa os testes unitários gerados |
| **Linguagem** | **Python 3.11.0** | — |

### LLMs suportados

O experimento foi desenhado para funcionar com 2 opções de LLM para escolha:

- **Gemini (padrão):** Rápido, via API, gratuito. Recomendado para desenvolvimento.
- **Ollama + CodeLlama (alternativa):** Roda localmente, sem necessidade de internet ou chave de API. Útil para comparar resultados entre modelos.

A escolha é feita pelo parâmetro `--llm` na execução.

## Opções de linha de comando

| Flag | Descrição | Padrão |
|---|---|---|
| `put` | Caminho do arquivo PUT (obrigatório) | — |
| `--llm` | LLM a usar: `gemini` ou `ollama` | `gemini` |
| `--shot` | Tipo de prompt: `zero` ou `few` | `zero` |
| `--max-iterations` | Máximo de iterações de aumento de prompt | `3` |
| `--test` | Arquivo de teste pré-existente (pula LLM) | — |
| `--no-minimize` | Pula a etapa de minimização greedy | `False` |
| `--mutants-dir` | Diretório para salvar/reutilizar arquivos mutantes | `generated-mutants` |

## Referências

- **Artigo original:** [Effective Test Generation Using Pre-trained Large Language Models and Mutation Testing](https://arxiv.org/abs/2308.16557) (arXiv:2308.16557)
- **Repositório oficial do MuTAP:** [github.com/ExpertiseModel/MuTAP](https://github.com/ExpertiseModel/MuTAP)
- **MutPy (ferramenta de mutação):** [github.com/boxed/mutpy](https://github.com/mutpy/mutpy), [página do PYPI](https://pypi.org/project/MutPy/)
- **Gemini API (LLM padrão):** [ai.google.dev](https://ai.google.dev/)
- **Ollama (LLM local):** [ollama.com](https://ollama.com/)

## Estrutura do projeto

```
mutap-demo/
├── README.md                   # Este arquivo
├── pyproject.toml              # Dependências (gerenciado pelo uv)
├── .env                        # Configurações (API key, etc.)
├── .env.example                # Modelo do .env
├── .gitignore
├── assets/                     # Imagens para documentação
│   ├── diagrama-mutap.png
│   └── mutation.png
├── generated-mutants/          # Mutantes gerados (reutilizáveis)
│   └── .gitkeep
├── put_examples/               # Funções para testar (PUTs)
│   ├── calculator.py           #   add(), divide(), is_even()
│   └── string_utils.py         #   reverse(), is_palindrome()
└── src/                        # Código fonte do pipeline
    ├── mutap_pipeline.py       # Orquestrador principal
    ├── llm_option.py           # Interface LLM (Gemini / Ollama)
    ├── prompts.py              # Templates de prompt (zero-shot, few-shot, aumentado)
    ├── mutation.py             # MutPy runner + parsing de saída + geração de arquivos mutantes
    ├── refinement.py           # Correção sintática de testes
    ├── semantic.py             # Correção semântica de asserções
    ├── minimization.py         # Minimização greedy de asserções
    └── utils.py                # Utilitários (path do MutPy, extract_code)
```

## Tutorial

### 1. Pré-requisitos

```bash
# Python 3.11
python --version  #ou python3 --version

# Instalar uv (gerenciador de pacotes)
pip install uv

# Instalar dependências (modo nativo)
uv sync
```

### 2. Configurar o LLM

**Opção A — Gemini (recomendado):**

1. Acesse [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Crie uma API key gratuita
3. Salve no arquivo `.env`:

```
GEMINI_API_KEY=sua_chave_aqui
```

**Opção B — Ollama (alternativa local):**

1. Instale o Ollama: [ollama.com](https://ollama.com/)
2. Baixe o modelo de código:

```bash
ollama pull codellama:7b-instruct
```

3. Defina no `.env` (opcional — estes são os valores padrão):

```
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=codellama:7b-instruct
```
### 3. Executar o pipeline

```bash
# Pipeline completo com Gemini
python src/mutap_pipeline.py put_examples/calculator.py

# Com Ollama
python src/mutap_pipeline.py put_examples/calculator.py --llm ollama

# Few-shot em vez de zero-shot
python src/mutap_pipeline.py put_examples/calculator.py --shot few

# Pular LLM, usar teste pré-existente (útil para testes)
python src/mutap_pipeline.py put_examples/calculator.py --test meu_teste.py

# Pular minimização greedy
python src/mutap_pipeline.py put_examples/calculator.py --no-minimize
```

O pipeline executa as seguintes etapas na ordem:

1. Carrega a função alvo (PUT)
2. LLM gera teste inicial (zero-shot ou few-shot)
3. **Correção semântica**: asserções com valores esperados errados são corrigidas automaticamente
4. MutPy gera mutantes e calcula Mutation Score inicial
5. Para cada mutante sobrevivente → prompt aumentado → LLM gera novo teste direcionado
6. **Minimização greedy**: remove asserções redundantes mantendo o MS máximo
7. Exibe teste final e MS

### Exemplo de saída (com `--test`)

```
╔════════════════════════════════════════════╗
║         MuTAP - Test Generation           ║
║   LLM + Mutation Testing Feedback Loop    ║
╚════════════════════════════════════════════╝

📄 PUT: calculator.py
🔤 LLM: GEMINI | Shot: zero

📄 Usando teste pré-carregado: /tmp/test_redundant.py
   → Teste:
     def test_add():
         assert add(2, 3) == 5
         assert add(-1, 1) == 0
         assert add(100, -50) == 50
     ...

🔧 Corrigindo erros semânticos...
   ✅ Nenhuma correção semântica necessária

🧬 Executando teste de mutação...
   → MS inicial: 100.0%
   → Mortos: 7  |  Sobreviventes: 0

📊 RESULTADO FINAL
   MS final: 100.0%

🔧 Aplicando minimização greedy...
   ✅ 9 → 3 asserções (-6)
   → MS após minimização: 100.0%

📄 Teste final:
   def test_add():
       assert add(2, 3) == 5
   def test_divide():
       assert divide(5, 2) == 2.5
   def test_is_even():
       assert is_even(4) is True
```
