# Guidelines de Arquitetura MVC

O padrão alvo é **MVC** (Model–View–Controller) adaptado a APIs HTTP modernas: "View" é a camada de roteamento (que recebe HTTP e devolve JSON), "Controller" orquestra o caso de uso, e "Model" representa os dados + acesso ao DB.

A regra de ouro: **uma classe/módulo, uma responsabilidade**. Se você precisa de dois `import` semanticamente distintos (DB e HTTP) no mesmo arquivo, provavelmente ele está fazendo duas coisas.

## Camadas e suas responsabilidades

```
┌──────────────────────────────────────────────────────┐
│  views/routes  →  só registra HTTP → controller     │
│  controllers   →  orquestra caso de uso             │
│  models        →  representa entidade + acesso DB    │
│  middlewares   →  cross-cutting (erro, log, auth)   │
│  config        →  settings, env vars, constantes    │
│  app (entry)   →  composition root                  │
└──────────────────────────────────────────────────────┘
```

### Models

Responsável por: **dados + persistência**.

Pode:
- Definir o schema (classes ORM, dataclasses).
- Encapsular queries (CRUD básico, scopes).
- Validar invariantes do dado (formato de email, faixa de prioridade).

Não pode:
- Importar `flask.request`, `express.Request`, `req`/`res`.
- Imprimir resposta HTTP.
- Tomar decisões de fluxo (ex.: "se admin, fazer X; senão, Y" → vai pro controller).

Um model por **agregado**. Se "Pedido" e "ItemPedido" sempre andam juntos, podem viver no mesmo arquivo. Se "Produto" e "Usuário" só se cruzam em pedidos, **separa**.

### Views / Routes

Responsável por: **mapear HTTP para uma chamada de controller**.

Pode:
- Registrar rotas (`app.add_url_rule`, `router.post`).
- Extrair params da request (`request.json`, `req.body`).
- Chamar o controller correspondente.

Não pode:
- Acessar DB diretamente.
- Conter regras de negócio.
- Formatar dados complexos (apenas serialização final).

Tamanho ideal: cada handler de rota cabe em 5-15 linhas (input → controller → response).

### Controllers

Responsável por: **um caso de uso**.

Pode:
- Validar input recebido pela rota.
- Chamar múltiplos models para compor uma operação.
- Disparar eventos secundários (enviar email, log de auditoria).
- Tratar erros de negócio (estoque insuficiente, usuário não existe).

Não pode:
- Conter SQL bruto (vai pro model).
- Acessar `request` diretamente (recebe parâmetros já extraídos pela view).
- Formatar respostas HTTP — devolve um objeto/dict que a view serializa.

Um controller por agregado, com métodos por caso de uso (`create`, `list`, `update_status`).

### Middlewares

Responsável por: **comportamento atravessado** (log, autenticação, tratamento de erro, CORS, rate limit).

Em Flask: `@app.errorhandler`, `@app.before_request`.
Em Express: funções `(req, res, next) => {}`.

Centralize error handling aqui — não em cada controller.

### Config

Responsável por: **carregar settings**.

Pode:
- Ler `os.environ` / `process.env` com fallbacks seguros.
- Expor constantes nomeadas (status válidos, listas de roles).

Não pode:
- Hardcode de secrets em produção.

Padrão Python:
```python
# config/settings.py
import os
from dataclasses import dataclass

@dataclass
class Settings:
    secret_key: str = os.environ.get("SECRET_KEY", "dev-only-change-me")
    debug: bool = os.environ.get("DEBUG", "false").lower() == "true"
    db_path: str = os.environ.get("DB_PATH", "loja.db")

settings = Settings()
```

Padrão Node:
```javascript
// config/settings.js
module.exports = {
    port: parseInt(process.env.PORT || '3000', 10),
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    nodeEnv: process.env.NODE_ENV || 'development',
};
```

### Entry point (composition root)

Responsável por: **montar a aplicação**.

Faz:
1. Carrega config.
2. Inicializa o app framework.
3. Registra middlewares (CORS, body parser, log).
4. Registra blueprints/routers.
5. Registra error handler.
6. Sobe o servidor (`app.run` / `app.listen`).

Tamanho ideal: 30-60 linhas.

---

## Estrutura de diretórios alvo

### Python/Flask

```
project-root/
├── app.py                       # entry compatível: from src.app import app
├── src/
│   ├── __init__.py
│   ├── app.py                   # cria + configura app, registra blueprints
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── infra/
│   │   ├── __init__.py
│   │   └── db.py                # init do SQLAlchemy / get_db sqlite3
│   ├── models/
│   │   ├── __init__.py
│   │   ├── produto_model.py
│   │   ├── usuario_model.py
│   │   ├── pedido_model.py
│   │   └── relatorio_model.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── produto_controller.py
│   │   ├── usuario_controller.py
│   │   └── pedido_controller.py
│   ├── views/
│   │   ├── __init__.py
│   │   └── routes.py            # registra todas as rotas
│   └── middlewares/
│       ├── __init__.py
│       └── error_handler.py
├── requirements.txt
└── reports/
    └── audit-report.md
```

### Node.js/Express

```
project-root/
├── package.json
├── src/
│   ├── app.js                   # composition root, sobe servidor
│   ├── config/
│   │   └── settings.js
│   ├── infra/
│   │   ├── db.js                # init sqlite3 / pool postgres
│   │   └── crypto.js            # bcrypt wrapper
│   ├── models/
│   │   ├── userModel.js
│   │   ├── courseModel.js
│   │   ├── enrollmentModel.js
│   │   └── paymentModel.js
│   ├── controllers/
│   │   ├── checkoutController.js
│   │   ├── userController.js
│   │   └── reportController.js
│   ├── views/
│   │   └── routes.js
│   └── middlewares/
│       ├── errorHandler.js
│       └── requestLogger.js
└── reports/
    └── audit-report.md
```

### Quando o projeto já tem alguma camada (caso task-manager-api)

Preserve nomes existentes quando fizer sentido. Por exemplo, se já existe `models/` e `routes/`, **mantenha**. Aumente o que falta:

- Falta `controllers/` → crie e mova a lógica de negócio das rotas.
- Falta `config/` → crie e extraia secrets.
- Falta `middlewares/error_handler.py` → crie.

Não reorganize por reorganizar. O objetivo é separar responsabilidades, não brigar com convenções existentes.

---

## Regras de dependência (direção das setas)

```
views/routes  ──→  controllers  ──→  models  ──→  infra/db
                     │
                     ↓
                  config (todos podem ler)
```

- Models **não importam** controllers.
- Controllers **não importam** views/routes.
- Views/routes **podem importar** controllers; controllers **podem importar** models.
- Middlewares são plugados pelo entry point, não importados de dentro de handlers.

Se você se ver fazendo `from views import routes` dentro de um controller, parou — vire o fluxo.

---

## Tratamento de erros centralizado

Em vez de `try/except` em cada handler retornando 500:

**Python/Flask:**
```python
# middlewares/error_handler.py
from flask import jsonify

class BusinessError(Exception):
    status_code = 400

class NotFoundError(BusinessError):
    status_code = 404

def register_error_handlers(app):
    @app.errorhandler(BusinessError)
    def handle_business(e):
        return jsonify({"erro": str(e), "sucesso": False}), e.status_code

    @app.errorhandler(Exception)
    def handle_generic(e):
        app.logger.exception(e)
        return jsonify({"erro": "Erro interno"}), 500
```

**Node/Express:**
```javascript
// middlewares/errorHandler.js
class BusinessError extends Error {
    constructor(message, statusCode = 400) { super(message); this.statusCode = statusCode; }
}

function errorHandler(err, req, res, next) {
    if (err instanceof BusinessError) return res.status(err.statusCode).json({ error: err.message });
    console.error(err.stack);
    return res.status(500).json({ error: 'Erro interno' });
}

module.exports = { BusinessError, errorHandler };
```

Plugar **uma única vez** no entry point. Controllers só lançam exceções; o middleware traduz para HTTP.

---

## Contrato de API

A refatoração **não pode** mudar:
- Verbos HTTP (`GET`, `POST`, `PUT`, `DELETE`).
- Paths (`/produtos`, `/api/checkout`).
- Estrutura dos JSON de entrada e saída.

Pode mudar:
- Implementação interna.
- Cabeçalhos não documentados.
- Mensagens de erro internas (mas mantenha as chaves: `{"erro": ...}` ou `{"error": ...}`, conforme o original).

Se identificar algo realmente irrecuperável (ex.: endpoint `/admin/query` que executa SQL arbitrário — anti-pattern AP-004), **remova** e documente no relatório como mudança intencional de contrato. Esse é o único caso em que mudar é aceitável: quando o endpoint original é uma vulnerabilidade ativa.
