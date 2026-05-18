# Playbook de Refatoração

Cada padrão tem: **gatilho** (qual anti-pattern resolve), **transformação** (o que fazer), e **exemplo antes/depois** em pelo menos uma das stacks-alvo (Python/Flask ou Node/Express). Use os exemplos como referência adaptável — adapte a sintaxe ao framework real do projeto.

Padrões neste playbook: **12** (acima do mínimo de 8 exigido).

---

## RP-01 — Extrair Configuração (resolve AP-002)

**Gatilho:** `SECRET_KEY = "..."`, `paymentGatewayKey: "pk_live_..."`, `DEBUG = True` hardcoded.

**Transformação:** mover todos os valores para `config/settings.{py,js}` que lê de env vars com defaults seguros, e usar `python-dotenv` / `dotenv` para suporte a `.env` local.

### Antes (Python)
```python
# app.py
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```

### Depois (Python)
```python
# src/config/settings.py
import os
from dataclasses import dataclass

@dataclass
class Settings:
    secret_key: str = os.environ.get("SECRET_KEY", "dev-only-change-me")
    debug: bool = os.environ.get("DEBUG", "false").lower() == "true"
    db_path: str = os.environ.get("DB_PATH", "loja.db")

settings = Settings()

# src/app.py
from .config.settings import settings
app.config["SECRET_KEY"] = settings.secret_key
app.config["DEBUG"] = settings.debug
```

### Antes (Node)
```javascript
// utils.js
const config = {
    dbUser: "admin_master",
    dbPass: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef",
};
```

### Depois (Node)
```javascript
// src/config/settings.js
module.exports = {
    dbUser: process.env.DB_USER || 'admin',
    dbPass: process.env.DB_PASS || '',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    port: parseInt(process.env.PORT || '3000', 10),
};
```

Crie `.env.example` para documentar os nomes das vars sem expor valores reais.

---

## RP-02 — Parametrizar SQL (resolve AP-001)

**Gatilho:** `cursor.execute("SELECT ... " + variable)` ou template strings com input externo.

**Transformação:** substituir concatenação por placeholders e tupla/array de parâmetros. Em ORM, usar a API.

### Antes (Python, sqlite3 puro)
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute(
    "INSERT INTO produtos (nome, preco) VALUES ('" + nome + "', " + str(preco) + ")"
)
```

### Depois (Python, sqlite3 puro)
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute(
    "INSERT INTO produtos (nome, preco) VALUES (?, ?)",
    (nome, preco),
)
```

### Depois (Python, SQLAlchemy)
```python
produto = Produto.query.filter_by(id=id).first()
produto = Produto(nome=nome, preco=preco)
db.session.add(produto)
db.session.commit()
```

### Antes/Depois (Node sqlite3)
```javascript
// Antes
this.db.run(`INSERT INTO users (email) VALUES ('${email}')`);
// Depois
this.db.run("INSERT INTO users (email) VALUES (?)", [email]);
```

---

## RP-03 — Hash de senha com bcrypt (resolve AP-003)

**Gatilho:** comparação direta de senha, `md5`, `sha1`, `base64`, função "homemade".

**Transformação:** usar `bcrypt` (ou `argon2`).

### Antes (Python)
```python
# models/user.py
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()
def check_password(self, pwd):
    return self.password == hashlib.md5(pwd.encode()).hexdigest()
```

### Depois (Python)
```python
# models/user.py
import bcrypt

def set_password(self, pwd: str) -> None:
    self.password = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def check_password(self, pwd: str) -> bool:
    return bcrypt.checkpw(pwd.encode(), self.password.encode())
```

Adicionar `bcrypt` ao `requirements.txt`.

### Antes/Depois (Node)
```javascript
// Antes
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    return hash.substring(0, 10);
}
// Depois — infra/crypto.js
const bcrypt = require('bcrypt');
async function hashPassword(pwd) { return bcrypt.hash(pwd, 10); }
async function verifyPassword(pwd, hash) { return bcrypt.compare(pwd, hash); }
module.exports = { hashPassword, verifyPassword };
```

---

## RP-04 — Quebrar God Class por agregado (resolve AP-005)

**Gatilho:** arquivo > 300 linhas com 3+ domínios.

**Transformação:** identificar agregados (Produto, Pedido, Usuário); criar `models/<agregado>_model.py` e `controllers/<agregado>_controller.py` para cada um; mover apenas o código relacionado àquele agregado.

### Plano de execução (sequência canônica)

1. Mapeie quais funções/métodos pertencem a cada agregado. Mark com prefixo mental.
2. Crie os arquivos de destino vazios.
3. Mova funções uma de cada vez; atualize imports nas chamadas.
4. Quebra os arquivos originais por último (mantenha temporariamente para evitar imports quebrados).
5. Quando tudo funcionar, delete o original.

Exemplo aplicado ao `models.py` do code-smells-project:

```
models.py (315 linhas)
  ├──→ models/produto_model.py    (CRUD de produtos + busca)
  ├──→ models/usuario_model.py    (CRUD de usuários + login)
  ├──→ models/pedido_model.py     (criar/listar pedidos + itens)
  └──→ models/relatorio_model.py  (relatorio_vendas)
```

E o `controllers.py` (293 linhas) espelha:
```
controllers.py
  ├──→ controllers/produto_controller.py
  ├──→ controllers/usuario_controller.py
  ├──→ controllers/pedido_controller.py
  └──→ controllers/relatorio_controller.py
```

---

## RP-05 — Mover lógica de negócio do Controller para Service (resolve AP-010)

**Gatilho:** handler de rota com cálculos, agregações, ou chamada de side effects.

**Transformação:** extrair o caso de uso para um service/use-case; o controller chama o service e formata resposta.

### Antes (Python)
```python
# routes/report_routes.py
@report_bp.route('/reports/summary')
def summary_report():
    # 80 linhas de queries, agregações, montagem de dicionário
    ...
```

### Depois (Python)
```python
# controllers/relatorio_controller.py
from flask import jsonify
from src.models import task_model, user_model

def summary_report():
    overview = task_model.contar_por_status()
    overdue = task_model.listar_overdue()
    user_stats = user_model.estatisticas_de_produtividade()
    return jsonify({"overview": overview, "overdue": overdue, "user_stats": user_stats})

# views/routes.py
from src.controllers import relatorio_controller
app.add_url_rule('/reports/summary', 'summary_report', relatorio_controller.summary_report, methods=['GET'])
```

A view só conhece o nome do handler; o controller orquestra; os models fazem as queries.

---

## RP-06 — Eliminar N+1 (resolve AP-020)

**Gatilho:** loop em `for x in rows: cursor.execute(...)` ou `forEach` com query interna.

**Transformação:** uma query única com `JOIN`, ou eager loading no ORM.

### Antes (Python, sqlite3)
```python
cursor.execute("SELECT * FROM pedidos")
for row in cursor.fetchall():
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
        ...
```

### Depois (Python, sqlite3)
```python
cursor.execute("""
    SELECT p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
           ip.produto_id, ip.quantidade, ip.preco_unitario,
           pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = ip.produto_id
    ORDER BY p.id
""")
# Agrupar em memória por pedido_id
```

### Depois (SQLAlchemy)
```python
from sqlalchemy.orm import selectinload
pedidos = Pedido.query.options(selectinload(Pedido.itens).selectinload(ItemPedido.produto)).all()
```

### Depois (Node, async/await + Promise.all)
```javascript
const courses = await all('SELECT * FROM courses');
const enrollments = await all('SELECT * FROM enrollments WHERE course_id IN (' + courses.map(() => '?').join(',') + ')', courses.map(c => c.id));
const userIds = [...new Set(enrollments.map(e => e.user_id))];
const users = await all('SELECT * FROM users WHERE id IN (' + userIds.map(() => '?').join(',') + ')', userIds);
// Agrupar em memória
```

Reduz N queries para 3 (ou 1 com JOIN).

---

## RP-07 — Promisificar callbacks (resolve AP-012)

**Gatilho:** Node `db.run(SQL, [...], cb)` aninhado, `let self = this`.

**Transformação:** envolver em `util.promisify` ou criar wrapper Promise. Usar `async/await` no handler.

### Antes (Node)
```javascript
app.post('/api/checkout', (req, res) => {
    this.db.get("SELECT ...", [cid], (err, course) => {
        if (err) return res.status(500).send("Erro");
        this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
            this.db.run("INSERT INTO enrollments ...", [u, cid], function(err) {
                self.db.run("INSERT INTO payments ...", [...], function(err) {
                    res.json({ ok: true });
                });
            });
        });
    });
});
```

### Depois (Node)
```javascript
// infra/db.js — promisify
const sqlite3 = require('sqlite3');
const { promisify } = require('util');
const db = new sqlite3.Database(':memory:');
db.run_async = promisify(db.run.bind(db));
db.get_async = promisify(db.get.bind(db));
db.all_async = promisify(db.all.bind(db));
module.exports = db;

// controllers/checkoutController.js
async function checkout(req, res, next) {
    try {
        const course = await db.get_async("SELECT * FROM courses WHERE id = ? AND active = 1", [req.body.courseId]);
        if (!course) return res.status(404).json({ error: 'Curso não encontrado' });
        const user = await userModel.findOrCreate(req.body.email, req.body.name, req.body.password);
        const enrollment = await enrollmentModel.create(user.id, course.id);
        await paymentModel.create(enrollment.id, course.price, paymentStatus(req.body.card));
        return res.status(200).json({ enrollment_id: enrollment.id });
    } catch (err) { next(err); }
}
```

---

## RP-08 — Transação para fluxo multi-etapa (resolve AP-014)

**Gatilho:** sequência de INSERT/UPDATE em tabelas relacionadas sem transação.

**Transformação:** envelopar em `BEGIN/COMMIT/ROLLBACK` ou `db.session.begin()`.

### Antes (Python, sqlite3)
```python
def criar_pedido(usuario_id, itens):
    cursor.execute("INSERT INTO pedidos ...")
    pedido_id = cursor.lastrowid
    for item in itens:
        cursor.execute("INSERT INTO itens_pedido ...")
        cursor.execute("UPDATE produtos SET estoque = estoque - ?")
    db.commit()
```

### Depois (Python, sqlite3)
```python
def criar_pedido(usuario_id, itens):
    db = get_db()
    try:
        db.execute("BEGIN")
        cursor = db.cursor()
        cursor.execute("INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)", (usuario_id, total))
        pedido_id = cursor.lastrowid
        for item in itens:
            cursor.execute("INSERT INTO itens_pedido (...) VALUES (?, ?, ?, ?)", (...))
            cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (item["quantidade"], item["produto_id"]))
        db.commit()
        return pedido_id
    except Exception:
        db.rollback()
        raise
```

---

## RP-09 — Centralizar tratamento de erros em middleware (resolve AP-022, AP-024)

**Gatilho:** `try/except` em cada handler retornando 500, ou `except:` bare.

**Transformação:** definir exceções de negócio + um único error handler.

### Depois (Python/Flask)
```python
# middlewares/error_handler.py
from flask import jsonify
import logging

logger = logging.getLogger(__name__)

class BusinessError(Exception):
    status_code = 400

class NotFoundError(BusinessError):
    status_code = 404

def register_error_handlers(app):
    @app.errorhandler(NotFoundError)
    def _not_found(e):
        return jsonify({"erro": str(e), "sucesso": False}), e.status_code

    @app.errorhandler(BusinessError)
    def _business(e):
        return jsonify({"erro": str(e), "sucesso": False}), e.status_code

    @app.errorhandler(Exception)
    def _generic(e):
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno"}), 500
```

Controllers passam a só lançar:
```python
def buscar_produto(id):
    produto = produto_model.por_id(id)
    if not produto:
        raise NotFoundError("Produto não encontrado")
    return jsonify({"dados": produto, "sucesso": True}), 200
```

### Depois (Node/Express)
```javascript
// middlewares/errorHandler.js
class BusinessError extends Error {
    constructor(message, statusCode = 400) { super(message); this.statusCode = statusCode; }
}
class NotFoundError extends BusinessError {
    constructor(message) { super(message, 404); }
}
function errorHandler(err, req, res, next) {
    if (err instanceof BusinessError) return res.status(err.statusCode).json({ error: err.message });
    console.error(err.stack);
    return res.status(500).json({ error: 'Erro interno' });
}
module.exports = { BusinessError, NotFoundError, errorHandler };

// src/app.js — sempre o último middleware
app.use(errorHandler);
```

---

## RP-10 — Remover endpoints admin perigosos (resolve AP-004)

**Gatilho:** `/admin/query`, `/admin/exec`, `eval` em rota.

**Transformação:** remover completamente o endpoint. Esse é o **único** caso em que mudar o contrato é aceitável — o endpoint era uma vulnerabilidade. Documentar no relatório.

Em vez de manter o endpoint, prover uma alternativa segura:
- Para reset de DB → script CLI (`python -m src.scripts.reset_db`) protegido por flag local.
- Para queries ad-hoc → console interativo (`flask shell`) acessível apenas localmente.

---

## RP-11 — Substituir API deprecated `datetime.utcnow` (resolve DEP-001)

**Gatilho:** `datetime.utcnow()`, `default=datetime.utcnow`.

**Transformação:** trocar por `datetime.now(timezone.utc)`.

### Antes
```python
from datetime import datetime
class Task(db.Model):
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Depois
```python
from datetime import datetime, timezone

def _now_utc():
    return datetime.now(timezone.utc)

class Task(db.Model):
    created_at = db.Column(db.DateTime, default=_now_utc)
    updated_at = db.Column(db.DateTime, default=_now_utc, onupdate=_now_utc)
```

Cuidado: comparar datetimes "naive" (sem tz) com "aware" lança `TypeError`. Padronize um lado.

---

## RP-12 — Sanitizar respostas (resolve AP-006)

**Gatilho:** `to_dict` incluindo `password`, `senha`, `card`; `/health` vazando `secret_key`.

**Transformação:** filtrar campos sensíveis em todo serializer; criar uma camada de DTO se preciso.

### Antes
```python
def to_dict(self):
    return {
        'id': self.id,
        'name': self.name,
        'email': self.email,
        'password': self.password,    # !!!
        'role': self.role,
    }
```

### Depois
```python
def to_dict(self, include_sensitive: bool = False):
    data = {
        'id': self.id,
        'name': self.name,
        'email': self.email,
        'role': self.role,
        'active': self.active,
    }
    # password nunca volta na API pública — não tem caso de uso legítimo
    return data
```

E remover do `/health`:
```python
@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'database': 'connected',
        # SEM secret_key, SEM db_path
    })
```

---

## Ordem de aplicação na Fase 3

Aplicar os padrões nesta sequência minimiza retrabalho:

1. **RP-01** — Extrair config (resolve secrets).
2. **RP-04** — Quebrar God Class (cria as camadas).
3. **RP-02** — Parametrizar SQL (uma vez que models existem).
4. **RP-03** — Hash bcrypt (modifica `models/user.py`).
5. **RP-05** — Mover lógica para controllers (uma vez que controllers existem).
6. **RP-09** — Centralizar erros.
7. **RP-08** — Transação no fluxo crítico.
8. **RP-07** — Promisificar callbacks (Node).
9. **RP-06** — Eliminar N+1.
10. **RP-10** — Remover endpoints perigosos.
11. **RP-11** — APIs deprecated.
12. **RP-12** — Sanitizar respostas.

Não é uma ordem rígida — adapte ao que cada projeto exige. Mas sempre **config + estrutura de pastas** primeiro; depois **segurança crítica**; depois **organização e perf**.
