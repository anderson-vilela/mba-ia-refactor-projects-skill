```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Dependencies:  flask-cors 4.0.0, marshmallow 3.20.1, requests 2.31.0, python-dotenv 1.0.0
Domain:        Task Manager API (tasks, users, categories, reports de produtividade)
Architecture:  MVC parcial — já existem models/, routes/, services/ e utils/, mas: (a) lógica de negócio mora dentro das routes; (b) falta camada controller dedicada; (c) config está hardcoded em app.py; (d) services tem apenas notification, com credenciais SMTP embutidas; (e) não há middleware de erro centralizado.
Source files:  11 files analyzed (app.py, database.py, seed.py + models/{task,user,category}.py + routes/{task,user,report}_routes.py + services/notification_service.py + utils/helpers.py)
DB tables:     tasks, users, categories
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask + Flask-SQLAlchemy
Files:   11 analyzed | ~830 lines of code
Date:    2026-05-18

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 5 | LOW: 5

## Findings

[CRITICAL] Senhas com MD5 (crypto broken)
File: models/user.py:29, 32
Description: set_password usa `hashlib.md5(pwd.encode()).hexdigest()`; check_password compara MD5 sem salt nem stretching.
Impact: MD5 está quebrado há ~20 anos; rainbow tables resolvem em segundos. Dump do banco = senhas dos usuários comprometidas em massa.
Recommendation: Substituir por bcrypt (`bcrypt.hashpw` / `bcrypt.checkpw`) conforme RP-03; migrar senhas no próximo login.

[CRITICAL] Senha sempre presente nas respostas
File: models/user.py:16-25
Description: User.to_dict inclui o campo `password` (o hash MD5). routes/user_routes.py:84-86, 129, 209 retornam to_dict() direto na resposta.
Impact: GET /users, GET /users/:id, POST /users (criação) e /login devolvem o hash da senha. Combinado com MD5, vira ataque off-line trivial.
Recommendation: Remover password do to_dict; criar UserPublicSchema conforme RP-12. Hash nunca sai por API.

[CRITICAL] Credenciais hardcoded (SECRET_KEY + SMTP)
File: app.py:13, services/notification_service.py:10-11
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` no fonte. NotificationService instancia com `email_user='taskmanager@gmail.com'`, `email_password='senha123'`.
Impact: Forja de sessões; comprometimento da conta SMTP; spoofing de emails legítimos do produto.
Recommendation: Mover para config/settings.py via env vars (RP-01); `.env.example` documentando keys; rotacionar credenciais SMTP.

[HIGH] Fake JWT no login
File: routes/user_routes.py:207-211
Description: Login devolve `'token': 'fake-jwt-token-' + str(user.id)`. Não é JWT real, não é assinado, não tem expiração.
Impact: Token previsível (sequencial pelo id); qualquer middleware de auth construído em cima é teatro.
Recommendation: Usar PyJWT/Authlib com SECRET_KEY de env, payload com `sub`/`exp`/`iat`; ou Flask-JWT-Extended.

[HIGH] Lógica de negócio dentro de routes
File: routes/report_routes.py:13-101
Description: summary_report executa 12 queries, agregações, loop sobre users, cálculos de percentual — tudo no handler. update_task (task_routes.py:156-223) re-implementa validação e atribui campos diretamente.
Impact: Não há serviço de relatório reutilizável; rotas viram God Functions; teste exige Flask client.
Recommendation: Extrair controllers/reportController e controllers/taskController; rotas só recebem, chamam, devolvem (RP-05).

[HIGH] Sem middleware de erro centralizado e `except` genérico engole stack
File: routes/task_routes.py:62-63, 137, 152-154, 222-223, 236-238; routes/user_routes.py:130-132, 149-151; routes/report_routes.py:186-188, 207-209, 221-223
Description: `try: ... except: return jsonify({'error': 'Erro ...'}), 500` repetido em cada handler. Alguns `except:` sem nome (bare). Sem logger.
Impact: Erros invisíveis em produção; mensagens genéricas escondem a causa; debugging quase impossível.
Recommendation: BusinessError / NotFoundError + middleware `@app.errorhandler` único (RP-09); logger configurado em app.py.

[HIGH] Estado mutável global no NotificationService
File: services/notification_service.py:5-11
Description: Lista `self.notifications` cresce indefinidamente em memória do processo. Credenciais SMTP carregadas no construtor.
Impact: Memory leak; reset só com restart; logs/notificações somem em deploy.
Recommendation: Persistir notificações em DB; injetar credenciais via config; usar pool ou serviço externo (Mailgun/SES).

[MEDIUM] N+1 query nas listagens de tasks
File: routes/task_routes.py:14-63
Description: `for t in tasks: User.query.get(t.user_id); Category.query.get(t.category_id)` — duas queries por task.
Impact: 100 tasks → 201 queries; latência ruim.
Recommendation: Eager loading com `selectinload(Task.user, Task.category)` ou JOIN explícito (RP-06).

[MEDIUM] Validação duplicada entre helpers, models e routes
File: utils/helpers.py:60-99, routes/task_routes.py:96-114, 156-184
Description: As mesmas regras (tamanho de título, faixa de prioridade, status válido, datas) existem em `process_task_data` (utils), `validate_status`/`validate_priority` (Task model) e inline nas rotas.
Impact: Drift inevitável; mudar uma sem mudar a outra cria bug; constantes VALID_STATUSES duplicadas (helpers e route).
Recommendation: Marshmallow schemas (já está nas deps!) para input; remover duplicações.

[MEDIUM] `type(x) == list` em vez de `isinstance`
File: routes/task_routes.py:141, 210, utils/helpers.py:103
Description: Comparação de tipo com `==` em vez de `isinstance`.
Impact: Subclasses de list quebram o ramo; estilo Python errado.
Recommendation: `isinstance(x, list)`; lintar com ruff.

[MEDIUM] DEP-001 — datetime.utcnow() (deprecated em Python 3.12+)
File: models/task.py:15-16, 51-52; models/user.py:14; routes/task_routes.py:31, 72, 285; routes/report_routes.py:35, 45, 71, 133; services/notification_service.py:35; utils/helpers.py:38
Description: Uso massivo de `datetime.utcnow()` e `default=datetime.utcnow`. Em Python 3.12+ emite DeprecationWarning; será removido em versões futuras.
Impact: Warnings poluem logs; quebra futura previsível.
Recommendation: Substituir por `datetime.now(timezone.utc)` em todos os lugares (RP-11).

[MEDIUM] CORS aberto, sem origin restrict
File: app.py:15
Description: `CORS(app)` sem `origins=`.
Impact: Front malicioso embarca chamadas; combinado com fake JWT (HIGH) e password no payload, é grave.
Recommendation: Lista de origens vinda de env var (RP-01).

[LOW] Imports não usados em vários arquivos
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6
Description: `import os, sys, json, datetime` em app.py mas só datetime é usado; routes/task_routes.py importa `json, os, sys, time` sem uso; routes/user_routes.py importa `hashlib, json` sem uso.
Impact: Ruído; falsos positivos em ferramenta de segurança que rastreia uso de hashlib.
Recommendation: `ruff` ou `flake8 + autoflake` resolve em uma linha.

[LOW] Print() como logging
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; utils/helpers.py:39-41
Description: print() para erro e auditoria; helpers.log_action também só faz print.
Impact: Sem nível, sem timestamp estruturado, sem arquivo. Inviável em produção.
Recommendation: `logging.getLogger(__name__)` + handler configurado uma única vez no entry point.

[LOW] Magic strings em valores válidos espalhadas
File: routes/task_routes.py:110, 177, models/task.py:39, utils/helpers.py:75, 110
Description: `['pending', 'in_progress', 'done', 'cancelled']` literal em 5 lugares; mesma situação para roles ('user', 'admin', 'manager') em 3 lugares.
Impact: Drift garantido; difícil acrescentar valor novo.
Recommendation: Enum (`enum.StrEnum`) ou constantes em config/constants.py centralizadas.

[LOW] CORS + CORS sem restrição (já listado em MEDIUM, omitir aqui).

[LOW] `to_dict` inconsistente entre models
File: models/task.py:23-36, models/user.py:16-25, models/category.py:13-21
Description: Cada model implementa to_dict diferente — task constrói dict campo a campo, user com literal, category usa var intermediária.
Impact: Estilo só; ainda assim, padronizar facilita leitura.
Recommendation: Mixin `Serializable` ou Marshmallow schemas (já está nas deps).

================================
Total: 17 findings
================================
```

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
