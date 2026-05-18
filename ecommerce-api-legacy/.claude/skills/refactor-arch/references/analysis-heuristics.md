# Heurísticas de Análise (Fase 1)

Como detectar linguagem, framework, banco de dados e arquitetura sem chutar. As heurísticas estão ordenadas da mais barata (olhar metadado) para a mais cara (ler código).

## 1. Detecção de Linguagem

Faça `ls` na raiz e cheque manifestos de dependências:

| Sinal | Linguagem inferida |
|---|---|
| `requirements.txt`, `Pipfile`, `pyproject.toml`, `setup.py`, `*.py` | **Python** |
| `package.json`, `package-lock.json`, `yarn.lock`, `*.js`, `*.ts` | **Node.js** (JS ou TS — cheque se há TS na lista de arquivos) |
| `Gemfile`, `*.rb` | **Ruby** |
| `composer.json`, `*.php` | **PHP** |
| `go.mod`, `*.go` | **Go** |
| `pom.xml`, `build.gradle`, `*.java` | **Java** |
| `Cargo.toml`, `*.rs` | **Rust** |
| `*.cs`, `*.csproj` | **C#/.NET** |

Se houver mais de um, eleja a linguagem do *entry point* (arquivo que sobe o servidor) como principal.

## 2. Detecção de Framework

### Python

Olhe `requirements.txt` / `pyproject.toml`. Padrões:

| Linha | Framework |
|---|---|
| `flask==X` | **Flask X** |
| `django==X` | **Django X** |
| `fastapi==X` | **FastAPI X** |
| `bottle`, `falcon`, `aiohttp`, `sanic`, `tornado` | nome do pacote |
| `flask-restful`, `flask-restx`, `flask-smorest` | Flask + plugin REST |
| `flask-sqlalchemy`, `sqlalchemy` | ORM SQLAlchemy |
| `peewee` | ORM Peewee |
| `sqlite3` (stdlib, sem ORM) | SQLite cru |

Se nenhuma dependência web aparecer mas há `import flask`, é Flask sem versão fixada.

### Node.js

Olhe `package.json` → `dependencies`:

| Pacote | Framework |
|---|---|
| `express` | **Express X.Y.Z** |
| `koa` | **Koa** |
| `fastify` | **Fastify** |
| `@nestjs/core` | **NestJS** |
| `hapi`, `@hapi/hapi` | **Hapi** |
| `next` | **Next.js** |
| `sqlite3`, `better-sqlite3` | SQLite cru |
| `mysql2`, `pg`, `mongoose`, `typeorm`, `prisma`, `sequelize` | DB driver/ORM correspondente |

### Outros ecossistemas

- **Ruby**: `Gemfile` com `rails`, `sinatra`, `roda`.
- **PHP**: `composer.json` com `laravel/framework`, `slim/slim`, `symfony/*`.
- **Go**: imports de `github.com/gin-gonic/gin`, `github.com/labstack/echo`, `net/http`.

## 3. Detecção do Entry Point

Em ordem de prioridade — pare no primeiro que encontrar:

1. Campo `scripts.start` no `package.json` (Node).
2. Campo `main` no `package.json`.
3. Convenções de nome: `app.py`, `main.py`, `server.py`, `manage.py`, `wsgi.py`, `asgi.py` (Python); `app.js`, `index.js`, `server.js`, `src/app.js`, `src/index.js` (Node).
4. Procure por `app.run(`, `app.listen(`, `uvicorn.run(`, `gunicorn` no código.

## 4. Detecção de Banco de Dados

### Banco em uso

| Sinal | Banco |
|---|---|
| `sqlite3.connect(`, `sqlite3.Database(`, `*.db` no diretório | **SQLite** |
| `psycopg2`, `pg`, `postgres://` em config | **PostgreSQL** |
| `pymysql`, `mysql2`, `mysql://` | **MySQL** |
| `mongoose`, `pymongo`, `mongodb://` | **MongoDB** |
| `redis` | **Redis** (cache, não como base principal) |
| `SQLALCHEMY_DATABASE_URI` no Flask | URI da string indica o banco |

### Schema (tabelas)

Procure por:
- `CREATE TABLE` (SQL bruto) — extraia o nome após `CREATE TABLE [IF NOT EXISTS]`.
- `class X(db.Model)` (SQLAlchemy) — `__tablename__` ou nome da classe.
- `class X(models.Model)` (Django).
- `mongoose.Schema` (Mongo).
- `sequelize.define(`, `prisma.model` (Node ORM).

Liste todas as tabelas encontradas na saída da Fase 1.

## 5. Detecção do Domínio

Combine pistas de:

- **Nome do diretório** (`ecommerce-api-legacy` → e-commerce; `task-manager-api` → gestão de tarefas).
- **Nomes de tabelas/modelos** (`produtos, pedidos, usuarios` → e-commerce; `tasks, categories` → task manager; `courses, enrollments, payments` → LMS/educação).
- **Paths de rotas** (`/api/checkout`, `/login`, `/relatorios/vendas`).
- **README.md** quando existir.

Descreva em uma frase curta. Exemplo: "E-commerce API (produtos, pedidos, usuários) com fluxo simples de catálogo e checkout."

## 6. Mapeamento da Arquitetura Atual

Classifique em uma das categorias:

| Categoria | Sinais |
|---|---|
| **Monolítica plana** | Tudo em 2-4 arquivos na raiz; `models.py`, `controllers.py`, `app.py` sem subpastas. |
| **God Class / God Module** | Um único arquivo > 300 linhas concentrando rotas, queries e regras (`AppManager.js`, `GodManager.py`). |
| **MVC parcial** | Existem `models/`, `routes/`, `services/`, mas: lógica de negócio mora nas rotas; falta camada controller dedicada; views inexistentes. |
| **MVC bem definido** | Camadas `models/`, `views/` (ou `routes/`), `controllers/` separadas e sem vazamento de responsabilidade. |

Na Fase 1, descreva o que **encontrou** em 1-2 linhas — sem julgamento ainda (esse vem na Fase 2).

## 7. Contagem de Arquivos de Código

Não conte:
- `node_modules/`, `__pycache__/`, `.venv/`, `dist/`, `build/`, `coverage/`
- `package-lock.json`, `yarn.lock`, arquivos binários, `.db` SQLite, `.env`
- READMEs e markdowns

Conte apenas arquivos da linguagem principal que tenham código executável (rotas, modelos, controllers, services, utils).

Comando útil:
```bash
# Python
find . -name "*.py" -not -path "./.venv/*" -not -path "./__pycache__/*" | wc -l
# Node
find . -name "*.js" -not -path "./node_modules/*" -not -path "./dist/*" | wc -l
```

## 8. Anti-padrões "óbvios" de Fase 1 (apenas anote, não classifique aqui)

Estes não vão para o relatório de auditoria ainda — são pistas para a Fase 2:

- Arquivos com nomes genéricos do tipo `utils.js`, `helpers.py`, `manager.js` (frequentemente God Module).
- Ausência total de subpastas → quase certo que falta separação.
- Diretório `controllers/` ausente, mas `routes/` presente → lógica está provavelmente nas rotas.
- `seed.py` / `seeders` no entry → mistura de bootstrap com runtime.

## 9. Formato de saída obrigatório

Após coletar tudo, imprima exatamente:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <Python/Node.js/...>
Framework:     <Flask 3.1.1 / Express 4.18.2 / ...>
Dependencies:  <flask-cors, flask-sqlalchemy, ...>
Domain:        <descrição curta>
Architecture:  <classificação + observação curta>
Source files:  <N> files analyzed
DB tables:     <produtos, usuarios, ...>
================================
```

Em seguida, parta para a Fase 2 sem perguntar.
