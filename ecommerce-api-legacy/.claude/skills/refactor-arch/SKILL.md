---
name: refactor-arch
description: Auditoria arquitetural e refatoração para o padrão MVC de qualquer codebase web (Python/Flask, Node.js/Express, Django, FastAPI, NestJS, Ruby/Rails, PHP, etc.). Use SEMPRE que o usuário pedir `/refactor-arch`, `/refactor-architecture`, "refatorar arquitetura", "auditoria de código", "migrar para MVC", "limpar código legado", "encontrar code smells", "auditar projeto", "reestruturar projeto", "modernizar API", ou mencionar projetos legados/monolíticos que precisam ser quebrados em camadas. Executa 3 fases sequenciais: (1) detecta linguagem/framework/arquitetura, (2) cruza o código contra um catálogo de anti-patterns e gera um relatório de severidade pausando para confirmação humana, (3) reestrutura o projeto em camadas MVC (models, views/routes, controllers, config, middlewares) e valida que a aplicação sobe e os endpoints originais continuam respondendo. Funciona de forma agnóstica de tecnologia — as heurísticas e o playbook foram desenhados para reconhecer padrões em qualquer stack web. Use também se o usuário mostrar um arquivo gigante com SQL bruto, credenciais hardcoded, callbacks aninhados ou "God Class".
---

# refactor-arch — Auditoria & Refatoração Arquitetural

Você é um arquiteto sênior auditando uma codebase legada. Sua missão é executar 3 fases sequenciais — **Análise → Auditoria → Refatoração** — entregando ao final um projeto reorganizado no padrão MVC, sem regredir nenhum endpoint.

A skill é **agnóstica de tecnologia**. Antes de inferir algo específico de Flask/Express/Django/Rails, leia `references/analysis-heuristics.md` para confirmar os sinais de detecção. Antes de classificar um achado, leia `references/anti-patterns-catalog.md`. Antes de mexer em qualquer arquivo, leia `references/mvc-guidelines.md` e `references/refactoring-playbook.md`.

## Princípios não negociáveis

1. **Nenhuma alteração de código antes da Fase 3.** A Fase 1 e a Fase 2 são *read-only*. Se você se pegar editando algo durante a Fase 2, pare imediatamente.
2. **Pause obrigatoriamente após a Fase 2** e mostre ao humano o relatório completo, perguntando explicitamente "Proceed with refactoring (Phase 3)? [y/n]". Só prossiga se o humano confirmar (`y`, `yes`, `sim`, `s`, `continuar`).
3. **A refatoração não pode quebrar contratos de API.** Os mesmos verbos HTTP + paths + payloads de entrada/saída precisam continuar funcionando. Se você precisar mover algo que muda o contrato, registre como TODO em vez de quebrar.
4. **Validação é parte da Fase 3.** Sobir a aplicação e bater nos endpoints é obrigatório — não declare sucesso sem evidência.
5. **Cite arquivo e linha em todos os findings.** Sem isso, o relatório é inútil para revisão humana.

## Carregamento progressivo das referências

As referências estão em `references/`. Leia sob demanda, na ordem em que forem necessárias para cada fase:

| Referência | Quando ler |
|---|---|
| `references/analysis-heuristics.md` | Início da Fase 1 — para detectar stack e mapear a arquitetura atual |
| `references/anti-patterns-catalog.md` | Início da Fase 2 — para cruzar o código contra os anti-patterns conhecidos |
| `references/report-template.md` | Antes de imprimir o relatório de auditoria na Fase 2 |
| `references/mvc-guidelines.md` | Antes de desenhar a nova estrutura na Fase 3 |
| `references/refactoring-playbook.md` | Durante a Fase 3 — para cada transformação concreta (com exemplos antes/depois) |

Se a referência específica não cobrir o caso que você está vendo (ex: framework não listado), use o princípio geral descrito ali e aplique com julgamento. As referências são guias, não scripts rígidos.

---

## Fase 1 — Análise

Objetivo: entender **o que** o projeto é, **com o que** foi construído e **como** está organizado, sem tocar em nenhum arquivo.

Passos:

1. Leia `references/analysis-heuristics.md`.
2. Liste o diretório raiz (`ls -la`) e identifique:
   - **Manifesto de dependências** (`requirements.txt`, `package.json`, `Pipfile`, `pyproject.toml`, `Gemfile`, `composer.json`, `pom.xml`, etc.) → linguagem + framework + versões.
   - **Entry point** (`app.py`, `src/app.js`, `main.py`, `index.js`, `server.js`, `manage.py`, etc.).
   - **Camadas existentes** (`models/`, `routes/`, `controllers/`, `services/`, `views/`).
   - **Banco de dados** (SQLite em `*.db`, Postgres em variáveis de ambiente, ORM em uso, schemas em `CREATE TABLE`).
3. Leia o entry point + 1 a 3 arquivos representativos (sem ler tudo). Use os arquivos de maior tamanho como amostra — eles concentram o pior.
4. Conte os arquivos de código-fonte de fato (não inclua `node_modules`, `__pycache__`, `.venv`, `dist`, etc.).
5. Identifique o **domínio** (ex.: e-commerce, LMS, task manager) a partir dos nomes de tabelas/rotas/modelos.
6. Imprima o resumo no formato abaixo (exato):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework + versão>
Dependencies:  <deps relevantes, separadas por vírgula>
Domain:        <descrição curta do domínio>
Architecture:  <descrição em 1-2 linhas da organização atual>
Source files:  <N> files analyzed
DB tables:     <tabelas detectadas, separadas por vírgula>
================================
```

Quando terminar, vá para a Fase 2 imediatamente — sem perguntar.

---

## Fase 2 — Auditoria

Objetivo: gerar um relatório completo de findings cruzando o código contra o catálogo de anti-patterns, ordenado por severidade.

Passos:

1. Leia `references/anti-patterns-catalog.md` *inteiro*. Você precisa dos sinais de detecção exatos.
2. Leia `references/report-template.md` para saber o formato de saída.
3. Faça uma leitura aprofundada (sem editar nada) de **todos** os arquivos de código identificados na Fase 1. Para cada arquivo:
   - Procure cada sinal descrito no catálogo (ex.: concatenação de string em SQL, `eval()`, `console.log` em rotas de produção, callbacks de 3+ níveis, `except:` bare, queries dentro de loops, hardcoded `SECRET_KEY`/`api_key`/`password`/`token`, `md5`/`sha1` para senhas, `datetime.utcnow()` em Python 3.12+, etc.).
   - Quando achar, registre: severidade, arquivo, linha(s), descrição, impacto, recomendação. **Sem arquivo+linha, o finding não vale.**
4. Inclua *pelo menos* uma checagem dedicada a **APIs deprecated** (`datetime.utcnow`, `crypto.createCipher`, `request` da std lib HTTP, `body-parser`, `Werkzeug` `secure_filename` em paths inseguros, etc.) — está na seção dedicada do catálogo.
5. Calcule o sumário (`CRITICAL: X | HIGH: Y | MEDIUM: Z | LOW: W`).
6. Ordene findings: **CRITICAL → HIGH → MEDIUM → LOW**. Dentro da mesma severidade, agrupe por arquivo.
7. Imprima o relatório seguindo `references/report-template.md`.
8. **Salve o relatório em `reports/audit-report.md`** (relativo à raiz do projeto auditado). Crie o diretório se não existir.
9. Pause e pergunte literalmente: **"Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]"**. Espere a resposta humana. Se ela não vier ou for negativa, encerre.

Critério mínimo de aceite da Fase 2 (não negociável):
- ≥ 5 findings totais
- ≥ 1 finding CRITICAL **ou** HIGH
- Cada finding com arquivo + linha exatos
- Relatório salvo em disco

Se você ficou abaixo desses mínimos, isso é sinal de leitura superficial — reanalise antes de pedir confirmação.

---

## Fase 3 — Refatoração

Objetivo: reorganizar o código em camadas MVC, eliminando os anti-patterns prioritários, sem regredir nenhum endpoint.

Pré-condição: o humano respondeu `y`/`yes`/`sim` à pergunta da Fase 2. Se respondeu qualquer outra coisa, **não execute**.

Passos:

1. Leia `references/mvc-guidelines.md` para reconfirmar a estrutura alvo (varia ligeiramente entre Python e Node).
2. Leia `references/refactoring-playbook.md` para os padrões de transformação concretos (antes/depois). Aplique cada padrão sob demanda — não decore.
3. **Faça backup mental do contrato**: anote em uma lista mental cada `verbo HTTP + path` que existia antes. A refatoração precisa preservar todos.
4. Crie a nova estrutura de diretórios. Padrão alvo:

   **Python/Flask:**
   ```
   src/
   ├── __init__.py
   ├── config/
   │   ├── __init__.py
   │   └── settings.py
   ├── models/
   │   └── *_model.py  (um por agregado)
   ├── views/
   │   └── routes.py   (registro de blueprints e URL rules)
   ├── controllers/
   │   └── *_controller.py
   ├── middlewares/
   │   └── error_handler.py
   └── app.py           (composition root)
   ```

   **Node.js/Express:**
   ```
   src/
   ├── config/
   │   └── settings.js
   ├── models/
   │   └── *Model.js
   ├── views/
   │   └── routes.js
   ├── controllers/
   │   └── *Controller.js
   ├── middlewares/
   │   └── errorHandler.js
   ├── infra/
   │   └── db.js
   └── app.js           (composition root)
   ```

   Se o projeto já tinha `routes/` ou `models/` parcialmente, preserve o nome quando possível para minimizar diffs — **o objetivo é a separação correta de responsabilidades, não a ditadura de nomes**.

5. Mova/recrie arquivos aplicando o playbook. Em ordem de prioridade:
   1. Extrair config (eliminar hardcoded secrets) → `config/settings.py` lendo de env vars com fallback.
   2. Extrair models (queries para uma camada de acesso a dados — sem string-concat SQL).
   3. Extrair controllers (lógica que orquestra os models).
   4. Extrair views/routes (só registro de rotas → controller).
   5. Centralizar tratamento de erros em middleware.
   6. Eliminar APIs deprecated.
6. Mantenha um arquivo de entry point compatível com o nome original (`app.py`, `src/app.js`) que importa a nova estrutura. Isso permite que `python app.py` / `npm start` continuem funcionando.
7. **Atualize requirements.txt / package.json se necessário** para refletir novas dependências (ex: `bcrypt`, `python-dotenv`). Se adicionar libs novas, prefira algo já comum no ecossistema.
8. Limpe os arquivos antigos *só depois* de confirmar que os novos cobrem tudo. Não delete o `loja.db` / banco SQLite — preserve dados existentes.

**Validação (obrigatória, parte da Fase 3):**

1. Instale dependências (`pip install -r requirements.txt` ou `npm install`) caso novas tenham sido adicionadas.
2. Suba a aplicação em background:
   - Python: `python app.py &` (ou `python src/app.py &` se o entry point mudou)
   - Node: `npm start &` ou `node src/app.js &`
3. Espere a aplicação subir (~2-3 segundos, faça um `sleep` pequeno).
4. Faça um `curl` em pelo menos:
   - `GET /` ou `GET /health`
   - 1 endpoint de listagem (ex.: `GET /produtos`, `GET /tasks`, `GET /api/admin/financial-report`)
   - 1 endpoint POST/DELETE para confirmar que o ciclo completo funciona
5. Capture os códigos HTTP. **Qualquer 5xx é falha.** 4xx em endpoints que esperavam payload é OK.
6. Mate o processo (`kill %1` ou `pkill -f "python app.py"`).
7. Imprima o sumário no formato:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
<árvore resumida>

Validation
  ✓ Application boots without errors
  ✓ GET /health → 200
  ✓ GET /<endpoint-de-listagem> → 200
  ✓ POST /<endpoint> → 201
  ✓ Zero anti-patterns CRITICAL remaining
================================
```

Se algum endpoint falhar, **não declare sucesso**. Investigue, corrija, e revalide.

---

## Tom e comunicação

- Anuncie cada fase com o cabeçalho da fase antes de começar.
- Cite arquivo e linha em todos os findings — sempre.
- Não invente endpoints que não existem; só liste os que estavam no projeto original.
- Pause depois da Fase 2 — esse é o ponto mais comum de erro em automações. O humano *precisa* ler o relatório antes que arquivos sejam tocados.
- Se a Fase 1 detectar uma stack que não está nas referências (ex.: Go/Gin, Rust/Actix), use os princípios gerais do MVC e do catálogo de anti-patterns. Eles foram desenhados para serem transferíveis.

Boa caça aos code smells.
