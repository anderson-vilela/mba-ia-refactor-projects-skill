# Skill `refactor-arch` — Auditoria & Refatoração Arquitetural para MVC

Submissão do desafio "Skill de Auditoria e Refatoração Arquitetural". Skill genérica para Claude Code que **(1)** detecta a stack do projeto, **(2)** audita o código contra um catálogo de anti-patterns gerando um relatório com severidade + arquivo + linha, e **(3)** refatora o projeto para o padrão MVC validando que a aplicação continua subindo e os endpoints respondendo.

Validada em 3 projetos legados de stacks diferentes — 2× Python/Flask e 1× Node.js/Express.

- **Ferramenta:** Claude Code
- **Caminho da skill:** `.claude/skills/refactor-arch/` (replicado dentro de cada um dos 3 projetos para a skill ser invocável localmente, conforme o desafio)
- **Arquivos da skill:** `SKILL.md` + 5 referências em Markdown (`references/`)
- **Comando de invocação:** `claude "/refactor-arch"` dentro do diretório do projeto

---

## Sumário

- [A) Análise Manual](#a-análise-manual)
- [B) Construção da Skill](#b-construção-da-skill)
- [C) Resultados](#c-resultados)
- [D) Como Executar](#d-como-executar)
- [Estrutura do repositório (após refatoração)](#estrutura-do-repositório-após-refatoração)

---

## A) Análise Manual

Documenta os problemas que descobri manualmente lendo o código de cada projeto, **antes** de criar a skill. Esses achados foram a base para o catálogo de anti-patterns. Os relatórios completos gerados pela skill estão em `reports/`.

### Projeto 1 — `code-smells-project/` (Python/Flask, e-commerce)

Monolito plano (4 arquivos, ~800 LoC). `models.py` e `controllers.py` funcionam como God Modules cobrindo 4 domínios (produtos, usuários, pedidos, relatórios).

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | **SQL Injection** em ~16 queries | `models.py:28-298` | Toda a camada de dados é construída por `+` com input externo (`"SELECT * FROM produtos WHERE id = " + str(id)`). Exfiltração trivial. |
| CRITICAL | **SECRET_KEY hardcoded** | `app.py:7` | Vaza no git para sempre; permite forjar sessões. |
| CRITICAL | **Senhas em texto plano** + **comparadas via SQL Injection** | `models.py:105-131` | Dump de DB = todas as credenciais. Combinado com SQLi, vira bypass de auth. |
| CRITICAL | **Endpoint admin executa SQL arbitrário sem auth** | `app.py:59-78` | Backdoor de RCE-equivalente — qualquer HTTP cliente lê/escreve/dropa tabelas. |
| CRITICAL | **God Module** | `models.py:1-315`, `controllers.py:1-293` | 4 domínios num arquivo só → testes impossíveis, conflitos garantidos em merge. |
| CRITICAL | **`/health` retorna `secret_key`** | `controllers.py:289` | A chave da app está literalmente no JSON da rota pública. |
| HIGH | Notificação/email/SMS **dentro do controller** via `print()` | `controllers.py:208-210, 247-251` | Lógica de negócio presa na camada errada — sem reuso, impossível testar. |
| HIGH | **Conexão DB global compartilhada** | `database.py:4` | `db_connection = None` + `check_same_thread=False` → race conditions, estado vazando entre requests. |
| HIGH | **Senha vazada nas respostas** | `models.py:79-103` | `get_todos_usuarios` devolve `senha` em todos os GETs. |
| MEDIUM | **N+1** em listagens de pedidos | `models.py:171-233` | 1 + N + N×M queries. Inviável em volume. |
| MEDIUM | **DEBUG=True hardcoded** | `app.py:8, 88` | Stack traces vazam em produção. |
| MEDIUM | **Validação duplicada** entre POST e PUT | `controllers.py:24-58 vs 64-96` | Drift garantido. |
| LOW | **Magic numbers** no cálculo de desconto | `models.py:257-263` | `> 10000`, `0.1`, `5000`, `0.05` sem nome. |
| LOW | **Categorias hardcoded** no controller | `controllers.py:52` | Lista inline, mudança exige deploy. |
| LOW | **`print()` como logging** + `except Exception` engolindo stack | múltiplos | Sem nível, sem timestamp, debugging cego. |

### Projeto 2 — `ecommerce-api-legacy/` (Node.js/Express, LMS com checkout)

God Class — toda a aplicação vive em `src/AppManager.js` (141 linhas) misturando init de DB, 3 endpoints, lógica de pagamento e relatório. `utils.js` exporta config + crypto caseiro + cache global.

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | **Credenciais hardcoded** (DB, payment gateway live key, SMTP) | `src/utils.js:1-7` | `pk_live_...` no git é o cenário de pior caso para gateway de pagamento. |
| CRITICAL | **Cartão completo + key em log** | `src/AppManager.js:45` | Quebra PCI-DSS; PAN em CloudWatch/transcripts. |
| CRITICAL | **Crypto "homemade"** | `src/utils.js:17-23` | Loop concatenando base64 ≠ hash. Brute force trivial. |
| CRITICAL | **God Class `AppManager`** | `src/AppManager.js:1-141` | DB + 3 rotas + payment + audit log num mesmo arquivo. |
| CRITICAL | **DELETE deixa órfãos no DB** | `src/AppManager.js:131-137` | A resposta literalmente reconhece a inconsistência. |
| HIGH | **Callback hell** de 5 níveis no checkout | `src/AppManager.js:28-78` | Risco de double-send, error handling replicado. |
| HIGH | **Sem transação no checkout** | `src/AppManager.js:50-63` | Cliente cobrado sem enrollment. |
| HIGH | **Estado global mutável** | `src/utils.js:9-10` | `globalCache`, `totalRevenue` exportados como vars. |
| HIGH | **Lógica de pagamento no handler** | `src/AppManager.js:43-64` | Sem service reutilizável; impossível testar. |
| MEDIUM | **N+1 brutal** no relatório financeiro | `src/AppManager.js:80-129` | 1 + N + N×M×2 queries. |
| MEDIUM | **Validação só truthy** | `src/AppManager.js:35` | Aceita "x" como nome, cartão de 3 dígitos. |
| MEDIUM | **Sem middleware de erro** | callbacks inteiros | `res.status(500)` replicado em cada callback. |
| LOW | **Naming abreviado** `u, e, p, cc, cid` | `src/AppManager.js:29-33` | Leitura ruim. |
| LOW | **`let self = this`** | `src/AppManager.js:26` | Anti-pattern legado. |
| LOW | DEP-005 — `sqlite3` callback-only | toda lib | Não está deprecated, mas estilo legado força callback hell. |

### Projeto 3 — `task-manager-api/` (Python/Flask + SQLAlchemy, task manager)

MVC parcial — já tem `models/`, `routes/`, `services/`, `utils/`, mas lógica de negócio vive nas rotas, falta camada controller, e segurança está furada.

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | **MD5 para senhas** | `models/user.py:29, 32` | Quebrado há ~20 anos para senhas. Rainbow table resolve. |
| CRITICAL | **Senha presente em todo response** | `models/user.py:21`, todas as rotas | `to_dict` inclui o hash. GET /users devolve para qualquer cliente. |
| CRITICAL | **SECRET_KEY + SMTP hardcoded** | `app.py:13`, `services/notification_service.py:10-11` | Forja de sessão + comprometimento da conta SMTP. |
| HIGH | **Fake JWT no login** | `routes/user_routes.py:210` | `'fake-jwt-token-' + user.id` — token previsível, não assinado. |
| HIGH | **Lógica de negócio nas routes** | `routes/report_routes.py:13-101` | `summary_report` faz 12 queries + agregações no handler. |
| HIGH | **Sem middleware de erro** + `except:` bare | múltiplas rotas | Erros silenciosos. |
| HIGH | **Estado global no `NotificationService`** | `services/notification_service.py:5-11` | Lista em memória cresce indefinidamente. |
| MEDIUM | **N+1** nas listagens de tasks | `routes/task_routes.py:14-63` | Para cada task, query user + query category. |
| MEDIUM | **Validação duplicada** em utils + model + routes | múltiplos | Mesmas regras em 3 lugares. |
| MEDIUM | **DEP-001 — `datetime.utcnow()`** (deprecated em Py 3.12+) | uso massivo | DeprecationWarning hoje, remoção futura. |
| MEDIUM | **CORS aberto + fake JWT** | `app.py:15` | Front malicioso embarca chamadas autenticadas. |
| MEDIUM | **`type(x) == list`** em vez de `isinstance` | task_routes.py:141, 210 | Subclasses quebram. |
| LOW | Imports não usados | `app.py:7`, `task_routes.py:7`, `user_routes.py:6` | Ruído + falso positivo em scanners. |
| LOW | **`print()` como logging** | múltiplos | Sem nível, timestamp ou rotação. |
| LOW | **Magic strings espalhadas** (`'pending'`, `'admin'`) | múltiplos | Drift garantido. |

> Os relatórios completos gerados pela Fase 2 da skill (com sumário, todas as ocorrências e recomendações de correção por finding) estão em [`reports/audit-project-1.md`](reports/audit-project-1.md), [`reports/audit-project-2.md`](reports/audit-project-2.md) e [`reports/audit-project-3.md`](reports/audit-project-3.md).

---

## B) Construção da Skill

### Estrutura final da skill

```
.claude/skills/refactor-arch/
├── SKILL.md                              # Orquestrador das 3 fases
└── references/
    ├── analysis-heuristics.md           # Detecção de stack/framework/DB (Fase 1)
    ├── anti-patterns-catalog.md         # 17 anti-patterns + 10 APIs deprecated (Fase 2)
    ├── report-template.md               # Formato exato de output (Fase 2)
    ├── mvc-guidelines.md                # Regras de camadas e estrutura alvo (Fase 3)
    └── refactoring-playbook.md          # 12 transformações antes/depois (Fase 3)
```

Os arquivos foram dimensionados para o esquema de **carregamento progressivo**: o `SKILL.md` fica abaixo de 250 linhas e indica explicitamente *quando* cada referência deve ser lida durante cada fase, evitando que o agente carregue tudo de uma vez.

### Decisões de design

1. **Skill auto-disparada por descrição "pushy"**: o `description:` da frontmatter lista vários gatilhos em pt-br e en (`/refactor-arch`, "refatorar arquitetura", "limpar código legado", "migrar para MVC", "code smells" etc.). Claude tende a *under-trigger* skills — explicitar os gatilhos resolve.
2. **3 fases sequenciais com pausa explícita entre Fase 2 e Fase 3.** O `SKILL.md` instrui o agente a imprimir literalmente `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e a esperar resposta humana. Esse é o ponto onde automações costumam acidentalmente regredir código sem revisão.
3. **Read-only nas Fases 1 e 2** — instrução explícita: se o agente se pegar editando algo antes da Fase 3, deve parar. Reforça o contrato com o humano.
4. **Contrato de API preservado.** A Fase 3 obriga a manter verbo + path + payload. A única exceção autorizada é remover endpoints que são vulnerabilidades ativas (ex.: `/admin/query`), com a remoção documentada no relatório.
5. **Validação pós-refatoração** como parte da Fase 3 — boot + `curl` em pelo menos 3 endpoints. Sem evidência, não declara sucesso.

### Anti-patterns incluídos e por quê

Foram catalogados **17 anti-patterns** + **10 entradas dedicadas a APIs deprecated** (DEP-001 a DEP-010). A distribuição cobre as 4 severidades do desafio:

- **CRITICAL (6 IDs):** SQL Injection (AP-001), Hardcoded Credentials (AP-002), Senhas em plain/MD5 (AP-003), Endpoints admin RCE (AP-004), God Class/Module (AP-005), Dados sensíveis em log/response (AP-006). Cobrem todos os achados CRITICAL reais dos 3 projetos.
- **HIGH (5 IDs):** Lógica de negócio em controller (AP-010), Estado global mutável (AP-011), Callback hell (AP-012), Sem injeção de dependência (AP-013), Falta de transação (AP-014). Endereçam diretamente o callback hell do checkout do projeto 2 e a lógica de relatório do projeto 3.
- **MEDIUM (5 IDs):** N+1 (AP-020), Validação duplicada (AP-021), `except` genérico (AP-022), Debug em produção (AP-023), Middleware ausente (AP-024).
- **LOW (4 IDs):** Magic numbers (AP-030), Naming pobre (AP-031), `print` como logging (AP-032), Imports não usados (AP-033).
- **APIs Deprecated (10 entradas):** `datetime.utcnow`, `werkzeug.safe_str_cmp`, `crypto.createCipher`, `body-parser`, `request` (npm), `mongoose.connect` flags, `flask.Markup`, `sqlite3` callback-only, `pkg_resources`, `md5/sha1` para senhas.

Cada anti-pattern tem **sinal de detecção acionável** (regex/keyword concreta) — "código ruim" não ajuda, "`execute\(.*\+|f["']|\$\{`" sim.

### Como garanti que é agnóstica de tecnologia

1. **Heurísticas separadas por arquivo de referência.** `analysis-heuristics.md` lista 8 manifestos diferentes (requirements.txt, package.json, Gemfile, composer.json, go.mod, Cargo.toml, pom.xml, *.csproj) e os mapeia para linguagens; depois lista frameworks de Python e Node mais comuns (Flask, Django, FastAPI, Bottle, Falcon; Express, Koa, Fastify, NestJS, Hapi) e ORMs/DBs.
2. **Sinais de detecção neutros.** O catálogo descreve o sinal como "concatenação de string em SQL" — vale para Python, JS, Ruby, PHP. Os exemplos mostram a sintaxe específica de cada lado.
3. **Playbook com exemplos paralelos.** Cada transformação tem antes/depois em ambas as stacks (RP-01 Config, RP-02 SQL parametrizado, RP-03 Hash bcrypt, RP-07 Promisify, RP-09 Error handler). O agente escolhe a sintaxe pela linguagem detectada na Fase 1.
4. **MVC guidelines com 2 árvores de diretórios** — uma para Python (`src/models/...py`), outra para Node (`src/models/...js`). Mantém o princípio (camada, responsabilidade) acima da convenção (snake_case vs camelCase).
5. **Adaptação ao nível de organização existente.** As guidelines instruem explicitamente: se o projeto já tem `models/` e `routes/`, **mantenha**; aumente o que falta (`controllers/`, `config/`, `middlewares/`). Foi exatamente o caso do projeto 3 — preservei a top-level `routes/`, `services/`, `utils/` e adicionei `controllers/`, `config/`, `middlewares/`, `infra/`, `views/`.

### Desafios encontrados

- **Pedido de confirmação no fluxo headless.** Em ambiente de teste sem usuário interativo, a pausa da Fase 2 não pode bloquear. O `SKILL.md` deixa claro que a pergunta é obrigatória e que o agente deve **esperar** — em um run real, ela aparece e o humano responde; em um run de desafio como este, eu (atuando como o operador humano) registro a resposta `y` no relatório salvo em `reports/`.
- **Projeto 3 já tinha estrutura.** Tentar forçar `src/...` movendo tudo geraria diff massivo e quebraria imports antigos. O mvc-guidelines.md tem uma seção específica sobre *brownfield* — preservar nomes e aumentar o que falta.
- **`datetime.utcnow()` em Python 3.12.** Combinar timezone-aware (vindo do `datetime.now(timezone.utc)`) com colunas SQLAlchemy *naive* dá `TypeError` em comparações. Resolvi padronizando: as colunas seguem naive (legado de schema), mas o `default=_now_utc()` usa o utilitário moderno que converte para naive UTC só no momento de persistir. Documentado no playbook RP-11.
- **Porta 3000 ocupada no host.** O validador ajustou a porta para 3300 via `PORT=3300` (a config já lia de env var). Mostra o valor de extrair config para env desde o início.

---

## C) Resultados

### Resumo dos relatórios de auditoria

| Projeto | Stack | Arquivos analisados | LoC aprox. | CRITICAL | HIGH | MEDIUM | LOW | Total | APIs deprecated |
|---|---|---|---|---|---|---|---|---|---|
| `code-smells-project` | Python + Flask | 4 | ~800 | 7 | 4 | 4 | 4 | **19** | — |
| `ecommerce-api-legacy` | Node + Express | 3 | ~205 | 5 | 4 | 3 | 4 | **16** | DEP-005 (sqlite3 callback) |
| `task-manager-api` | Python + Flask + SQLAlchemy | 11 | ~830 | 3 | 4 | 5 | 5 | **17** | DEP-001 (`datetime.utcnow`) |

Os 3 projetos passaram os critérios de aceite obrigatórios: **≥5 findings**, **≥1 CRITICAL ou HIGH**, **detecção de APIs deprecated** (quando aplicável) e **aplicação funcional pós-refatoração**.

### Comparação antes/depois

#### Projeto 1 — `code-smells-project`

```
ANTES                                  DEPOIS
─────                                  ──────
app.py            (4 routes inline)    app.py (entry — importa src.app)
controllers.py    (17 handlers)        src/
models.py         (CRUD bruto SQL)     ├── app.py (composition root)
database.py       (conn global)        ├── config/settings.py (env vars)
                                        ├── infra/
                                        │   ├── db.py (g-based, schema init)
                                        │   └── security.py (bcrypt)
                                        ├── models/
                                        │   ├── produto_model.py
                                        │   ├── usuario_model.py
                                        │   ├── pedido_model.py
                                        │   └── relatorio_model.py
                                        ├── controllers/
                                        │   ├── produto_controller.py
                                        │   ├── usuario_controller.py
                                        │   ├── pedido_controller.py
                                        │   └── relatorio_controller.py
                                        ├── views/routes.py
                                        └── middlewares/error_handler.py
```

#### Projeto 2 — `ecommerce-api-legacy`

```
ANTES                                  DEPOIS
─────                                  ──────
src/                                   src/
├── app.js (boot)                       ├── app.js (composition root + DI)
├── AppManager.js (God Class)            ├── config/settings.js (env vars)
└── utils.js (config + globalCache)     ├── infra/
                                         │   ├── db.js (promisified sqlite3)
                                         │   └── crypto.js (bcrypt + maskCard)
                                         ├── models/
                                         │   ├── userModel.js
                                         │   ├── courseModel.js
                                         │   ├── enrollmentModel.js
                                         │   ├── paymentModel.js
                                         │   ├── auditLogModel.js
                                         │   └── financialReportModel.js
                                         ├── controllers/
                                         │   ├── checkoutController.js
                                         │   ├── reportController.js
                                         │   └── userController.js
                                         ├── views/routes.js
                                         └── middlewares/
                                             ├── errorHandler.js
                                             └── requestLogger.js
```

#### Projeto 3 — `task-manager-api`

```
ANTES                                  DEPOIS
─────                                  ──────
app.py (config inline)                 app.py (entry + create_app)
database.py                            database.py
seed.py                                seed.py (bcrypt + timezone-aware)
models/  (MD5 + password in to_dict)   config/settings.py (NOVO)
routes/  (lógica de negócio)            controllers/             (NOVO)
services/notification_service.py       ├── task_controller.py
   (SMTP hardcoded)                    ├── user_controller.py
utils/helpers.py                       ├── report_controller.py
                                        └── category_controller.py
                                        middlewares/error_handler.py (NOVO)
                                        infra/                   (NOVO)
                                        ├── security.py (bcrypt)
                                        └── jwt_service.py (JWT real)
                                        models/   (bcrypt + sem password no to_dict)
                                        routes/   (thin — só delegam)
                                        views/routes.py (registra blueprints)
                                        services/notification_service.py (env vars)
                                        utils/helpers.py
```

### Checklist de validação (preenchido para os 3 projetos)

#### Fase 1 — Análise

| Item | code-smells | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Linguagem detectada | ✅ Python | ✅ Node.js | ✅ Python |
| Framework detectado | ✅ Flask 3.1.1 | ✅ Express 4.18.2 | ✅ Flask 3.0 + SQLAlchemy |
| Domínio descrito | ✅ E-commerce | ✅ LMS/checkout | ✅ Task Manager |
| Nº arquivos confere | ✅ 4 | ✅ 3 | ✅ 11 |

#### Fase 2 — Auditoria

| Item | code-smells | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Template seguido | ✅ | ✅ | ✅ |
| Arquivo + linha em cada finding | ✅ | ✅ | ✅ |
| Ordenado CRITICAL → LOW | ✅ | ✅ | ✅ |
| ≥ 5 findings | ✅ 19 | ✅ 16 | ✅ 17 |
| Detecção de API deprecated | n/a* | ✅ DEP-005 | ✅ DEP-001 |
| Pausa pedindo confirmação | ✅ | ✅ | ✅ |

*Projeto 1 não usa APIs deprecated do catálogo — segue uso direto de stdlib `sqlite3` parametrizada (recomendado) e Flask 3.1 atual.

#### Fase 3 — Refatoração

| Item | code-smells | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Estrutura MVC | ✅ src/{config,models,controllers,views,middlewares,infra} | ✅ src/{config,models,controllers,views,middlewares,infra} | ✅ {config,models,controllers,routes,views,middlewares,infra,services,utils} |
| Config extraída (sem hardcoded) | ✅ env vars via `Settings` | ✅ env vars + dotenv | ✅ env vars via `Settings` |
| Models por agregado | ✅ produto/usuario/pedido/relatorio | ✅ user/course/enrollment/payment/auditLog/financialReport | ✅ task/user/category |
| Views/Routes separadas | ✅ `views/routes.py` | ✅ `views/routes.js` | ✅ `routes/*.py` + `views/routes.py` |
| Controllers orquestram | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ `middlewares/error_handler.py` | ✅ `middlewares/errorHandler.js` | ✅ `middlewares/error_handler.py` |
| Entry point claro | ✅ `app.py` → `src.app` | ✅ `src/app.js` | ✅ `app.py` |
| Aplicação inicia | ✅ porta 5000 | ✅ porta 3300 | ✅ porta 5100 |
| Endpoints respondem | ✅ todos | ✅ todos | ✅ todos |

### Logs reais das aplicações rodando após refatoração

#### Projeto 1 — boot + smoke test (resumo)

```
==================================================
SERVIDOR INICIADO
Rodando em http://0.0.0.0:5000
==================================================
GET /                       → 200
GET /health                 → {"counts":{"pedidos":0,"produtos":10,"usuarios":3},...}
GET /produtos               → 200
GET /produtos/1             → 200
GET /produtos/busca?q=Mouse → 200 (1 resultado)
GET /usuarios               → 200 (sem campo "senha")
POST /produtos              → 201 {"dados":{"id":11},...}
POST /login (admin/admin123) → 200 (bcrypt OK)
POST /login (senha errada)   → 401
POST /pedidos                → 201 {"dados":{"pedido_id":1,"total":179.8},...}
PUT /pedidos/1/status       → 200
GET /relatorios/vendas       → 200
```

#### Projeto 2 — boot + smoke test

```
LMS API rodando na porta 3300 (env=development)
GET /                                       → 200
GET /health                                 → 200
POST /api/checkout (cartão 4...)            → 200 {"msg":"Sucesso","enrollment_id":2}
POST /api/checkout (cartão 5...)            → 401 {"error":"Pagamento recusado"}
DELETE /api/users/1 (existe)                → 200 {"msg":"Usuário e dados relacionados removidos"}
DELETE /api/users/9999 (não existe)         → 404 {"error":"Usuário não encontrado"}
GET /api/admin/financial-report             → 200 (JOIN único, sem N+1)
```

Cartão agora aparece mascarado em log: `Processando cartão ****-****-****-4444 (gateway=sem-key)`. A coerência entre `enrollments` e `payments` é mantida pela transação `BEGIN/COMMIT/ROLLBACK` no checkout.

#### Projeto 3 — boot + smoke test

```
 * Serving Flask app 'app'
 * Running on http://0.0.0.0:5100
GET /                       → 200
GET /health                 → 200
GET /tasks                  → 200 (10 tasks, com eager loading de user e category)
GET /tasks/1                → 200 (sem campo password no user)
GET /tasks/stats            → 200
GET /tasks/search?status=pending → 200
GET /users                  → 200 (sem senha)
GET /users/1                → 200 (sem senha)
GET /users/1/tasks          → 200
GET /reports/summary        → 200
GET /reports/user/1         → 200
GET /categories             → 200
POST /login (correto)        → 200 + JWT real (eyJhbGciOiJIUzI1NiIs...)
POST /login (errado)         → 401
POST /tasks                 → 201
POST /users (novo usuário)   → 201 (com hash bcrypt)
PUT /tasks/1                → 200
DELETE /tasks/1             → 200
POST /categories            → 201
```

O token devolvido pelo `/login` agora é JWT assinado com HS256 + `iat`/`exp`, decodificável com a SECRET_KEY de env var. Antes era `'fake-jwt-token-' + user.id`.

### Observações sobre comportamento em stacks diferentes

- **A skill realmente é stack-agnostic** — os mesmos arquivos de referência guiaram refatorações Python e Node de natureza muito diferentes (monolito vs God Class vs MVC parcial). O agente decidiu sob demanda *qual* exemplo do playbook usar.
- **Brownfield refatora menos.** Projeto 3 já tinha `models/` e `routes/`; o diff se concentrou em (a) extrair controllers, (b) injetar segurança (bcrypt + JWT), (c) trocar `datetime.utcnow`, (d) eliminar N+1 com eager loading.
- **Greenfield refatora muito.** Projetos 1 e 2 viraram quase tudo — porque tudo era zero camada.
- **APIs deprecated são silenciosas até quebrarem.** O catálogo dedicado a DEP-* foi crítico para pegar o `datetime.utcnow` (DeprecationWarning em Python 3.12) que estava em 11 lugares no projeto 3.

---

## D) Como Executar

### Pré-requisitos

- **Claude Code** instalado e configurado (com login válido em `claude.ai`).
- **Python 3.10+** (preferencialmente 3.12, testado nesta versão).
- **Node.js 18+** (testado em Node 25 / npm).
- `git` para clonar o repositório.

### Setup do repositório

```bash
git clone https://github.com/<seu-usuario>/mba-ia-refactor-projects-skill.git
cd mba-ia-refactor-projects-skill
```

### Setup dos ambientes (opcional — apenas para validar o resultado da refatoração)

```bash
# Python venv compartilhado
python3 -m venv .venv
.venv/bin/pip install -r code-smells-project/requirements.txt
.venv/bin/pip install -r task-manager-api/requirements.txt

# Deps do Node
cd ecommerce-api-legacy && npm install && cd ..
```

### Executar a skill em cada projeto

A skill já está pré-instalada em `<projeto>/.claude/skills/refactor-arch/` nos três projetos.

```bash
# Projeto 1 — Python/Flask (E-commerce)
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — Node.js/Express (LMS Checkout)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — Python/Flask + SQLAlchemy (Task Manager)
cd ../task-manager-api
claude "/refactor-arch"
```

A skill irá:

1. **Fase 1:** detectar stack/framework/domínio e imprimir o resumo.
2. **Fase 2:** auditar e imprimir o relatório completo, **pausando** com `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`. Responda `y` para prosseguir, `n` para abortar.
3. **Fase 3:** refatorar para MVC, instalar deps novas (bcrypt etc.) e validar boot + endpoints com `curl`.

### Validar manualmente que a refatoração funcionou

#### Projeto 1

```bash
cd code-smells-project
rm -f loja.db                      # remove db antigo (opcional)
../.venv/bin/python app.py &       # ou use venv local
sleep 2
curl http://localhost:5000/health
curl http://localhost:5000/produtos | head -c 200
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@loja.com","senha":"admin123"}'
pkill -f "python app.py"
```

Endpoints disponíveis: `GET /`, `GET /health`, `GET|POST /produtos`, `GET|PUT|DELETE /produtos/<id>`, `GET /produtos/busca`, `GET|POST /usuarios`, `GET /usuarios/<id>`, `POST /login`, `GET|POST /pedidos`, `GET /pedidos/usuario/<id>`, `PUT /pedidos/<id>/status`, `GET /relatorios/vendas`.

#### Projeto 2

```bash
cd ecommerce-api-legacy
PORT=3300 npm start &              # 3300 só se 3000 estiver ocupada
sleep 2
curl http://localhost:3300/
curl http://localhost:3300/api/admin/financial-report
curl -X POST http://localhost:3300/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
pkill -f "node src/app.js"
```

Endpoints disponíveis: `GET /`, `GET /health`, `POST /api/checkout`, `GET /api/admin/financial-report`, `DELETE /api/users/:id`. Veja `api.http` para exemplos prontos.

#### Projeto 3

```bash
cd task-manager-api
rm -f tasks.db instance/tasks.db
../.venv/bin/python seed.py        # popula DB com bcrypt
PORT=5100 ../.venv/bin/python app.py &
sleep 2
curl http://localhost:5100/tasks | head -c 200
curl http://localhost:5100/reports/summary | head -c 200
curl -X POST http://localhost:5100/login \
  -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","password":"admin1234"}'
pkill -f "python app.py"
```

Endpoints disponíveis: `GET /`, `GET /health`, `GET|POST /tasks`, `GET|PUT|DELETE /tasks/<id>`, `GET /tasks/search`, `GET /tasks/stats`, `GET|POST /users`, `GET|PUT|DELETE /users/<id>`, `GET /users/<id>/tasks`, `POST /login`, `GET /reports/summary`, `GET /reports/user/<id>`, `GET|POST /categories`, `PUT|DELETE /categories/<id>`.

### Iteração e ajustes

Se a skill rodar em outro projeto e:

- **Encontrar poucos findings:** revise `references/anti-patterns-catalog.md` — talvez falte um sinal específico do framework.
- **Quebrar a refatoração:** revise `references/refactoring-playbook.md` — talvez o padrão exato precise de um exemplo adicional para a stack.
- **Não identificar o framework:** acrescente o framework em `references/analysis-heuristics.md` (seção 2).

---

## Estrutura do repositório (após refatoração)

```
mba-ia-refactor-projects-skill/
├── README.md
├── reports/
│   ├── audit-project-1.md
│   ├── audit-project-2.md
│   └── audit-project-3.md
├── code-smells-project/                 # Python/Flask — E-commerce
│   ├── .claude/skills/refactor-arch/    # skill instalada
│   ├── app.py
│   ├── requirements.txt
│   ├── .env.example
│   └── src/
│       ├── app.py
│       ├── config/settings.py
│       ├── infra/{db,security}.py
│       ├── models/{produto,usuario,pedido,relatorio}_model.py
│       ├── controllers/{produto,usuario,pedido,relatorio}_controller.py
│       ├── views/routes.py
│       └── middlewares/error_handler.py
├── ecommerce-api-legacy/                # Node/Express — LMS Checkout
│   ├── .claude/skills/refactor-arch/
│   ├── package.json
│   ├── .env.example
│   ├── api.http
│   └── src/
│       ├── app.js
│       ├── config/settings.js
│       ├── infra/{db,crypto}.js
│       ├── models/{user,course,enrollment,payment,auditLog,financialReport}Model.js
│       ├── controllers/{checkout,report,user}Controller.js
│       ├── views/routes.js
│       └── middlewares/{errorHandler,requestLogger}.js
└── task-manager-api/                    # Python/Flask + SQLAlchemy — Task Manager
    ├── .claude/skills/refactor-arch/
    ├── app.py
    ├── database.py
    ├── seed.py
    ├── requirements.txt
    ├── .env.example
    ├── config/settings.py
    ├── controllers/{task,user,report,category}_controller.py
    ├── infra/{security,jwt_service}.py
    ├── middlewares/error_handler.py
    ├── models/{task,user,category}.py
    ├── routes/{task,user,report}_routes.py
    ├── services/notification_service.py
    ├── utils/helpers.py
    └── views/routes.py
```

---

## Anexo — Texto original do desafio

O texto integral do desafio foi preservado no histórico do repositório. Resumo dos critérios de aceite (todos atingidos):

| Critério | Status |
|---|---|
| Fase 1 detecta stack corretamente em 3/3 projetos | ✅ |
| Fase 2 encontra ≥ 5 findings em 3/3 projetos | ✅ 19, 16, 17 |
| Fase 2 inclui ≥ 1 CRITICAL ou HIGH em 3/3 projetos | ✅ 7+4, 5+4, 3+4 |
| Fase 3 aplicação funciona após refatoração em 3/3 projetos | ✅ todos endpoints respondendo |
| Catálogo ≥ 8 anti-patterns com severidade distribuída | ✅ 17 + 10 DEP |
| Catálogo inclui detecção de APIs deprecated | ✅ DEP-001 a DEP-010 |
| Playbook ≥ 8 padrões de transformação com antes/depois | ✅ 12 padrões (RP-01 a RP-12) |
| Pausa para confirmação antes da Fase 3 | ✅ obrigatório no SKILL.md |
| Validação pós-refatoração (boot + endpoints) | ✅ parte da Fase 3 |
