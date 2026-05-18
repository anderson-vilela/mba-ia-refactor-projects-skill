# Catálogo de Anti-Patterns

Cada anti-pattern tem: **ID**, **severidade**, **sinais de detecção** (acionáveis, com regex/keywords concretas) e **impacto**. Use este catálogo para cruzar contra o código na Fase 2.

A escala de severidade segue a definição do desafio:

- **CRITICAL** — segurança grave, arquitetura quebrada por completo, exposição de credenciais.
- **HIGH** — viola MVC/SOLID, lógica de negócio em camada errada, estado global mutável.
- **MEDIUM** — performance, duplicação, validação dispersa.
- **LOW** — legibilidade, nomenclatura, magic numbers.

Sumário de anti-patterns neste catálogo: **17** no total — distribuídos entre CRITICAL/HIGH/MEDIUM/LOW + uma seção dedicada a **APIs deprecated**.

---

## CRITICAL

### AP-001 — SQL Injection por concatenação de string

Severidade: **CRITICAL**

Sinais de detecção:
- `cursor.execute("SELECT ... " + variavel)` ou `cursor.execute(f"... {variavel}")` (Python).
- `db.run("... " + req.body.x)`, template strings com `${}` em SQL bruto (Node).
- Qualquer SQL que use `+` ou interpolação de string com input do usuário.

Padrão regex: `execute\([^)]*(\+|f["']|\$\{)` → forte suspeita.

Impacto: atacante consegue executar SQL arbitrário (`'; DROP TABLE users; --`) e exfiltrar/danificar dados.

Recomendação: usar parâmetros nomeados/posicionais (`?` no SQLite, `%s` no psycopg2, prepared statements). Em ORMs, usar a API nativa.

---

### AP-002 — Hardcoded Credentials / Secrets

Severidade: **CRITICAL**

Sinais de detecção:
- `SECRET_KEY = "..."`, `api_key = "..."`, `password = "..."`, `dbPass = "..."` literais no código.
- Chaves do tipo `sk_live_`, `pk_live_`, `AKIA*`, `eyJ*` (formato JWT/AWS).
- SMTP user/pass, Stripe keys, OAuth client_secret no fonte.

Padrão regex: `(secret_key|api_key|password|token|pwd|secret)\s*[:=]\s*["'][^"']{6,}["']` (case insensitive).

Impacto: vaza em git, código compartilhado, logs, dumps. Compromete todas as integrações.

Recomendação: mover para variáveis de ambiente, lidas via `os.environ`/`process.env` com `.env` no `.gitignore`.

---

### AP-003 — Senhas em texto plano ou hash quebrado

Severidade: **CRITICAL**

Sinais de detecção:
- `SELECT * FROM users WHERE password = '<senha>'` (comparação direta).
- `hashlib.md5(`, `hashlib.sha1(`, `crypto.createHash('md5')`, `crypto.createHash('sha1')` para senhas.
- `Buffer.from(pwd).toString('base64')` — base64 não é hash.
- Funções "homemade" tipo `badCrypto`, `myEncrypt`, loops manuais sobre charcode.

Impacto: rainbow tables / força bruta triviais. MD5 e SHA1 estão quebrados há mais de uma década para senhas.

Recomendação: `bcrypt`, `argon2`, `scrypt`, ou no mínimo `pbkdf2` com salt. Em Python: `bcrypt` ou `passlib`. Em Node: `bcrypt` ou `argon2`.

---

### AP-004 — Endpoint admin sem autenticação executando código/SQL arbitrário

Severidade: **CRITICAL**

Sinais de detecção:
- Rotas tipo `/admin/query`, `/admin/exec`, `/eval`, `/debug` que aceitam body com SQL ou código e executam.
- `eval()`, `exec()`, `Function()` recebendo input do usuário.
- `cursor.execute(request.get_json()["sql"])`.

Impacto: RCE / SQL arbitrário, exfiltração total do banco.

Recomendação: remover. Se necessário, mover para CLI/console interno protegido por auth + IP allowlist.

---

### AP-005 — God Class / God Module

Severidade: **CRITICAL** (quando 4+ domínios juntos) ou **HIGH** (quando 2-3 domínios)

Sinais de detecção:
- Arquivo único com > 300 linhas misturando: setup do servidor, rotas, queries SQL, regras de negócio, formatação de saída.
- Classes com > 10 métodos públicos cobrindo domínios diferentes (`AppManager`, `BusinessLogic`).
- Diversas tabelas/agregados manipulados no mesmo arquivo.

Impacto: impossível testar em isolamento; qualquer mudança ricocheteia em tudo; merges geram conflitos constantes.

Recomendação: quebrar por agregado/domínio. Um arquivo de model por entidade, um controller por agregado.

---

### AP-006 — Dados sensíveis em logs ou em payloads de resposta

Severidade: **CRITICAL**

Sinais de detecção:
- `console.log(card)`, `print(senha)`, `logger.info(api_key)` com dados sensíveis na string.
- `to_dict` / `serialize` incluindo campo `password`, `senha`, `card_number`, `cvv`.
- Endpoint `/health` ou `/debug` retornando `secret_key`, `db_path`, etc.

Impacto: dados sensíveis em CloudWatch / Datadog / Stackdriver, vazam em prints, em telas de erro, em transcripts.

Recomendação: nunca logar PII/credenciais. Em respostas, sempre filtrar campos sensíveis.

---

## HIGH

### AP-010 — Lógica de negócio dentro de Controllers / Routes

Severidade: **HIGH**

Sinais de detecção:
- Rota/handler que faz: cálculo de descontos, validações de regra de negócio, formatação complexa, agregações.
- Funções de rota com > 30 linhas.
- `print("ENVIANDO EMAIL ...")` dentro do handler.

Impacto: regra de negócio não pode ser reutilizada em outras rotas, em CLI, em jobs. Difícil de testar.

Recomendação: extrair para um service/use case. Controller só orquestra: valida input → chama service → formata resposta.

---

### AP-011 — Estado global mutável

Severidade: **HIGH**

Sinais de detecção:
- Variáveis no topo do módulo modificadas em runtime: `db_connection = None`, `cache = {}`, `total_revenue = 0`.
- `global X` dentro de funções.
- Singletons mutáveis sem proteção contra concorrência.

Impacto: race conditions, estado vazando entre requisições, testes não isolados.

Recomendação: injetar dependências (DI). Conexão de DB via factory / `g` do Flask / contexto do request.

---

### AP-012 — Callback hell / Acoplamento de fluxo assíncrono profundo

Severidade: **HIGH**

Sinais de detecção (Node):
- Handlers com 3+ níveis de callbacks aninhados.
- Uso de `db.run(SQL, [...], cb)` dentro de outro `db.run` etc.
- `let self = this` para preservar contexto em callbacks.

Impacto: leitura ruim, tratamento de erro inconsistente, fácil esquecer um `return` e enviar resposta duas vezes.

Recomendação: promisify (`util.promisify` ou wrapper Promise) e usar `async/await`. Em projetos novos, use `better-sqlite3` (síncrono) ou Prisma.

---

### AP-013 — Sem injeção de dependência / acoplamento direto

Severidade: **HIGH**

Sinais de detecção:
- Controller importa diretamente o cliente de DB / SMTP / HTTP.
- `from database import db` no topo de cada controller.
- `new EmailService()` instanciado dentro de cada handler.

Impacto: impossível trocar implementação em teste; cada controller carrega tudo.

Recomendação: receber dependências via parâmetro (constructor injection) ou via container/registry.

---

### AP-014 — Falta de transação em operação multi-etapa

Severidade: **HIGH**

Sinais de detecção:
- Sequência de `INSERT/UPDATE` em tabelas diferentes (ex.: pedido → itens → estoque) sem `BEGIN`/`COMMIT`/`ROLLBACK`.
- Em Node sqlite3, várias chamadas `db.run` para o mesmo fluxo de checkout.
- Sem `try/except` que faça rollback.

Impacto: deixar dados inconsistentes (pedido criado mas estoque não decrementado).

Recomendação: usar transações explícitas. SQLAlchemy: `with db.session.begin():`. sqlite3 puro: `BEGIN; ... COMMIT;`.

---

## MEDIUM

### AP-020 — N+1 Query

Severidade: **MEDIUM** (ou **HIGH** se em endpoint de listagem com volume alto)

Sinais de detecção:
- `for x in rows:` seguido de outra query `db.execute(...)` dentro do loop.
- `forEach` em Node disparando queries adicionais para cada item.
- Carregamento de relacionados (user, category) item a item.

Impacto: latência cresce linearmente com o número de itens; trava o DB.

Recomendação: usar `JOIN`; em ORM, `selectinload`, `joinedload`, `populate`/`include`. Em SQL bruto, fazer uma única query com `LEFT JOIN`.

---

### AP-021 — Validação duplicada e dispersa

Severidade: **MEDIUM**

Sinais de detecção:
- As mesmas regras de validação (tamanho de título, faixa de prioridade) repetidas em POST e PUT.
- Validações tanto em utils quanto em routes/controllers.

Impacto: drift — uma muda, outra não. Bug em produção.

Recomendação: criar schemas/DTOs (marshmallow, pydantic, joi, yup) e validar via middleware ou no controller, uma vez.

---

### AP-022 — Tratamento de exceção genérico (`except:` / `catch(err)` engolindo erros)

Severidade: **MEDIUM**

Sinais de detecção:
- `except:` sem nome (Python).
- `try: ... except Exception: pass`.
- `catch (e) { /* nada */ }` ou retorno de erro genérico sem log.

Impacto: bugs invisíveis em produção, sem stack trace.

Recomendação: capturar exceções específicas; logar com stack; centralizar em middleware de erro.

---

### AP-023 — Debug ativo / configuração de desenvolvimento em produção

Severidade: **MEDIUM**

Sinais de detecção:
- `app.config["DEBUG"] = True` hardcoded.
- `app.run(debug=True)`.
- `NODE_ENV` não consultado; `morgan('dev')` sem chave de feature flag.

Impacto: stack traces vazam em respostas; reload automático em prod consome recursos.

Recomendação: ler de env var; default seguro (`False`/`production`).

---

### AP-024 — Middlewares ausentes ou mal posicionados

Severidade: **MEDIUM**

Sinais de detecção:
- Sem middleware de log de request.
- Sem `cors` controlado (ou `CORS(app)` sem origin restrict).
- Sem rate limiting em endpoints sensíveis (`/login`).
- Tratamento de erro replicado em cada handler em vez de um único `errorHandler`.

Impacto: superfície de ataque maior; duplicação no controller.

Recomendação: cadeia de middlewares: log → cors → body parser → auth → handler → errorHandler.

---

## LOW

### AP-030 — Magic numbers / strings sem nome

Severidade: **LOW**

Sinais de detecção:
- Limiares numéricos no meio da regra (`if faturamento > 10000`, `* 0.1`).
- Strings de domínio espalhadas (`"pendente"`, `"aprovado"`, `"PAID"`) sem enum.

Recomendação: constantes nomeadas em `config/constants.py` ou enums.

---

### AP-031 — Naming pobre / abreviações

Severidade: **LOW**

Sinais de detecção:
- Variáveis `u`, `e`, `p`, `cid`, `cc` representando entidades.
- Métodos `doStuff`, `process`, `handle1`.

Recomendação: substantivos e verbos descritivos: `user`, `email`, `password`, `courseId`, `creditCard`.

---

### AP-032 — `print` / `console.log` como logging

Severidade: **LOW**

Sinais de detecção:
- `print("ERRO: " + str(e))` no controller.
- `console.log(...)` para informar sucesso de operação.

Recomendação: usar `logging` (Python) / `winston`/`pino` (Node), com níveis (INFO/WARN/ERROR) e formato estruturado.

---

### AP-033 — Imports não usados / `from X import *`

Severidade: **LOW**

Sinais de detecção:
- `import os, sys, json, datetime` quando só `datetime` é usado.
- `from utils import *`.

Recomendação: limpar imports; ferramentas como `ruff`, `eslint --fix` resolvem automaticamente.

---

## APIs Deprecated (seção dedicada)

A presença de qualquer um destes é finding obrigatório.

### DEP-001 — `datetime.utcnow()` em Python ≥ 3.12

Severidade: **MEDIUM** (warning hoje; remoção futura).

Sinais: `datetime.utcnow()`, `default=datetime.utcnow` em modelos SQLAlchemy.

Substituir por: `datetime.now(timezone.utc)`.

### DEP-002 — `werkzeug.utils.safe_join` (removido) / `werkzeug.security.safe_str_cmp` (removido)

Severidade: **HIGH** se o código depende disso.

Substituir `safe_str_cmp` por `hmac.compare_digest`.

### DEP-003 — `crypto.createCipher` (Node, deprecated desde 10.x, removido em 22)

Severidade: **HIGH**.

Substituir por `crypto.createCipheriv` com IV explícito.

### DEP-004 — `body-parser` standalone (Node)

Severidade: **LOW**.

Express 4.16+ inclui `express.json()` e `express.urlencoded()` nativamente. Remover dependência `body-parser`.

### DEP-005 — `request` (npm) — abandonada em fev/2020

Severidade: **MEDIUM**.

Substituir por `node-fetch`, `axios`, ou o `fetch` nativo (Node 18+).

### DEP-006 — `mongoose.connect` com `useNewUrlParser`/`useUnifiedTopology`

Severidade: **LOW**.

Em Mongoose 6+, essas opções são default. Remover para limpar warnings.

### DEP-007 — `flask.Markup`, `flask.escape`

Severidade: **LOW**.

Movidas para `markupsafe`. Importar de `markupsafe` em vez de `flask`.

### DEP-008 — `sqlite3` Node — interface puramente callback

Severidade: **MEDIUM**.

Recomendar `better-sqlite3` (síncrono, mais rápido) ou wrapper Promise. Não está literalmente deprecated, mas é considerada legado.

### DEP-009 — `pkg_resources` (Python)

Severidade: **LOW**.

Substituir por `importlib.metadata` em Python 3.10+.

### DEP-010 — `hashlib.md5`/`hashlib.sha1` para senhas (relacionado a AP-003)

Severidade: **CRITICAL** quando aplicado a senhas/tokens.

Já coberto em AP-003 mas vale reforçar — algoritmos não-deprecated em si, **mas obsoletos para esse caso de uso**.

---

## Como cruzar contra o código

1. Para cada arquivo da Fase 1, leia integralmente.
2. Para cada anti-pattern relevante (em ordem de severidade), procure os sinais.
3. Se achar, anote: `[AP-XXX|severidade] arquivo:linha-inicial(-linha-final) — descrição contextualizada → impacto → recomendação`.
4. Não duplique: se o mesmo arquivo viola AP-001 em 10 lugares, agrupe ("models.py:28-300 — SQL Injection em todas as queries do módulo").

Use os sinais como gatilho; o julgamento humano vem do contexto. Um `hashlib.md5` em deduplicação de cache não é CRITICAL — só vira CRITICAL se for senha.
