```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1, sqlite3 (stdlib)
Domain:        E-commerce API (produtos, pedidos, usuários, relatórios de vendas)
Architecture:  Monolítica plana — 4 arquivos na raiz, sem subpastas, sem separação por domínio. models.py e controllers.py funcionam como God Modules.
Source files:  4 files analyzed (app.py, controllers.py, models.py, database.py — ~800 LoC)
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code
Date:    2026-05-18

## Summary
CRITICAL: 7 | HIGH: 4 | MEDIUM: 4 | LOW: 4

## Findings

[CRITICAL] SQL Injection por concatenação de string
File: models.py:28-298
Description: Praticamente todas as queries em models.py constroem o SQL via "+" com input externo — `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))`. Padrão repetido em models.py:28, 47-50, 58-60, 68, 92, 109-111, 126-128, 140, 155-156, 174, 188, 220, 224, 279-281 e 289-298 (buscar_produtos chega a concatenar LIKE com `termo`).
Impact: Atacante pode injetar SQL arbitrário via path params, query string ou JSON e exfiltrar usuarios/pedidos, dropar tabelas ou bypassar login.
Recommendation: Substituir todas as queries por placeholders parametrizados ("?", "(?, ?)") com tupla de parâmetros, conforme RP-02.

[CRITICAL] Hardcoded SECRET_KEY
File: app.py:7
Description: app.config["SECRET_KEY"] = "minha-chave-super-secreta-123" — chave de assinatura literal no fonte.
Impact: Quem clonar o repositório consegue forjar sessões/tokens assinados; vaza no git para sempre.
Recommendation: Mover para env var via config/settings.py (RP-01), com default seguro só para desenvolvimento.

[CRITICAL] Senhas em texto plano
File: models.py:105-131
Description: login_usuario compara senha diretamente: `WHERE email = '<e>' AND senha = '<s>'`. criar_usuario insere a senha bruta sem hash. Não há sequer SHA1 — é texto puro no banco.
Impact: Dump do banco entrega todas as credenciais. Sessão pode ser falsificada por SQL Injection (AP-001) trivialmente.
Recommendation: Hash com bcrypt no set/check de senha conforme RP-03; migrar dados existentes via script.

[CRITICAL] Endpoint admin executando SQL arbitrário sem autenticação
File: app.py:59-78
Description: POST /admin/query aceita {"sql": "..."} e executa direto no banco; retorna resultados em SELECT, faz commit em qualquer outro comando.
Impact: RCE-equivalente — qualquer cliente HTTP consegue ler/escrever/dropar tudo. É a definição de backdoor.
Recommendation: Remover o endpoint (RP-10). Reset/queries ad-hoc só via CLI local autenticada.

[CRITICAL] Endpoint admin de reset sem autenticação
File: app.py:47-57
Description: POST /admin/reset-db apaga itens_pedido, pedidos, produtos e usuarios sem qualquer auth.
Impact: Destruição total do banco por qualquer requisição autenticada ou anônima.
Recommendation: Remover do roteamento HTTP; mover para script CLI sob `flask shell`/comando dedicado.

[CRITICAL] God Module — models.py
File: models.py:1-315
Description: 315 linhas misturando CRUD de produtos, usuários, pedidos, itens, login, busca e relatório de vendas. 4 agregados num único arquivo, com cálculos de desconto e formatação de saída acoplados ao acesso a dados.
Impact: Impossível testar agregados isoladamente; mudanças em pedidos quebram busca de produtos; merge conflict garantido.
Recommendation: Quebrar em models/produto_model.py, models/usuario_model.py, models/pedido_model.py e models/relatorio_model.py (RP-04).

[CRITICAL] Dados sensíveis vazando no /health
File: controllers.py:264-292
Description: Resposta do /health retorna campos `db_path`, `debug` e literalmente `"secret_key": "minha-chave-super-secreta-123"`.
Impact: Qualquer cliente HTTP descobre a SECRET_KEY sem nenhum esforço de exploração.
Recommendation: Health check só responde {status, database, counts}. Sanitizar serialização conforme RP-12.

[HIGH] Lógica de negócio dentro de controllers
File: controllers.py:188-220
Description: criar_pedido dispara "envio de email", "envio de SMS" e "push notification" via print() direto no handler. atualizar_status_pedido (controllers.py:237-255) imprime notificações de aprovação/cancelamento.
Impact: Notificação não pode ser reutilizada por job/CLI; controller cresce indefinidamente; impossível mockar em teste.
Recommendation: Extrair NotificationService injetado; controller só orquestra. Padrão RP-05.

[HIGH] God Module — controllers.py
File: controllers.py:1-293
Description: 293 linhas com 17 handlers cobrindo produtos, usuários, pedidos e relatório. Mesma raiz do problema em models.py.
Impact: Cada PR mexe no mesmo arquivo; difícil rastrear dono lógico de cada endpoint.
Recommendation: Espelhar a quebra do model: controllers/produto_controller.py, usuario_controller.py, pedido_controller.py, relatorio_controller.py.

[HIGH] Estado global mutável da conexão
File: database.py:4
Description: db_connection = None no topo do módulo, modificada pelo get_db(). Mesma conexão compartilhada entre todas as requests (check_same_thread=False).
Impact: Race conditions sob carga; impossível usar transações isoladas; testes vazam estado.
Recommendation: Usar `g` do Flask + teardown, ou SQLAlchemy session por request. Padrão RP-01 + RP-09.

[HIGH] Senha exposta nas respostas de listagem
File: models.py:79-103
Description: get_todos_usuarios e get_usuario_por_id retornam o campo `senha` no dicionário serializado.
Impact: GET /usuarios devolve todas as senhas em texto plano. Combinado com a falta de hash (AP-003), é a falha de segurança mais alta possível.
Recommendation: Remover campo senha do to_dict; criar serializer dedicado conforme RP-12.

[MEDIUM] N+1 query em listagens de pedidos
File: models.py:171-233
Description: get_pedidos_usuario e get_todos_pedidos iteram sobre pedidos e, dentro do for, fazem nova query para itens_pedido e outra para produtos. 1 + N + N×M queries.
Impact: Lista 50 pedidos com 3 itens cada → 251 queries. Latência cresce com o volume.
Recommendation: Substituir por single JOIN agrupado em memória (RP-06).

[MEDIUM] Debug ativo em "produção"
File: app.py:8, 88
Description: app.config["DEBUG"]=True e app.run(debug=True, host="0.0.0.0") hardcoded. Werkzeug reload + stack traces vazam em qualquer ambiente.
Impact: Stack traces revelam estrutura interna; reload consome recursos; pin remoto possível em alguns cenários.
Recommendation: Ler DEBUG de env var com default False (RP-01).

[MEDIUM] Validação duplicada entre POST e PUT de produto
File: controllers.py:24-58, 64-96
Description: criar_produto e atualizar_produto repetem byte-a-byte as mesmas 8 validações (nome, preço, estoque, categoria).
Impact: Mudar uma regra exige editar dois lugares; drift é só questão de tempo.
Recommendation: Extrair validate_produto_payload para utilitário/serializer único.

[MEDIUM] Tratamento de erro genérico engolindo stack
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 124-126, 133-134, 143-144, 164-165, 185-186, 219-220, 226-227, 234-235, 254-255, 261-262, 291-292
Description: 16 handlers retornam `jsonify({"erro": str(e)}), 500` em `except Exception`, sem logger nem stack — só o `print()` quando muito.
Impact: Erros silenciosos em produção; mensagens reveladoras do interno chegam no cliente.
Recommendation: Middleware único de erro (RP-09) + logging estruturado; controllers só levantam exceções de negócio.

[LOW] Magic numbers no cálculo de desconto
File: models.py:257-263
Description: faturamento > 10000 → 10%; > 5000 → 5%; > 1000 → 2%. Sem constantes nem comentário.
Impact: Ninguém revisa a regra ao mudar valores; teste fica frágil.
Recommendation: Mover para constantes nomeadas em config (FAIXAS_DESCONTO) ou tabela em DB.

[LOW] Lista de categorias hardcoded no controller
File: controllers.py:52
Description: categorias_validas = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"] inline no handler.
Impact: Mudar categoria exige deploy; lista pode divergir entre POST e UPDATE.
Recommendation: Mover para config/constants.py.

[LOW] Uso de print() como logging
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250, models.py:* (várias)
Description: print() espalhado para sucesso ("Produto criado"), erro ("ERRO CRITICO") e até notificação fake (envio de email).
Impact: Sem nível, sem timestamp estruturado; difícil filtrar em CloudWatch/Datadog.
Recommendation: Substituir por `logging.getLogger(__name__)` com níveis (info/error).

[LOW] CORS totalmente aberto
File: app.py:9
Description: `CORS(app)` sem restrição de origin.
Impact: Front malicioso embarca chamadas autenticadas; superfície de CSRF aumentada.
Recommendation: Restringir `origins=` para lista vinda de env var.

================================
Total: 19 findings
================================
```

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
