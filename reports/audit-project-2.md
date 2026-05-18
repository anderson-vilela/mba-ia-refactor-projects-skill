```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Node.js (JavaScript, CommonJS)
Framework:     Express 4.18.2
Dependencies:  sqlite3 5.1.6
Domain:        LMS API (cursos, matrículas, pagamentos, auditoria) com fluxo de checkout
Architecture:  God Class — toda a aplicação está em src/AppManager.js (141 linhas misturando DB init, roteamento, regras de checkout, relatório financeiro, exclusão de usuário). app.js é só boot.
Source files:  3 files analyzed (src/app.js, src/AppManager.js, src/utils.js)
DB tables:     users, courses, enrollments, payments, audit_logs
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express
Files:   3 analyzed | ~205 lines of code
Date:    2026-05-18

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 3 | LOW: 4

## Findings

[CRITICAL] Credenciais hardcoded (DB, gateway de pagamento, SMTP)
File: src/utils.js:1-7
Description: Objeto `config` exporta dbUser, dbPass ("senha_super_secreta_prod_123"), paymentGatewayKey ("pk_live_1234567890abcdef") e smtpUser literalmente no fonte.
Impact: Chave de gateway live + credencial de DB no git → comprometimento total dos serviços externos.
Recommendation: Mover para process.env via config/settings.js (RP-01); rodar `git filter-repo` para purgar histórico após rotacionar segredos.

[CRITICAL] Cartão de crédito completo e chave de gateway em log
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` imprime PAN completo + chave de produção.
Impact: PCI-DSS quebrado; vaza em arquivos de log, em sistemas como CloudWatch/Datadog, transcripts de terminal. Multa regulatória + fraude.
Recommendation: Nunca logar PAN; mascarar para `****-****-****-1234`. Não logar a key. Padrão RP-12.

[CRITICAL] Senhas com crypto "homemade" inseguro
File: src/utils.js:17-23
Description: `badCrypto` faz loop de 10000 iterações concatenando substring de base64 → não é hash, é truncamento previsível.
Impact: Trivial fazer brute force ou colisão; combinado com PAN logado, comprometimento total.
Recommendation: Substituir por bcrypt (`bcrypt.hash`/`bcrypt.compare`) conforme RP-03.

[CRITICAL] God Class AppManager
File: src/AppManager.js:1-141
Description: Uma classe contém init de DB, três endpoints HTTP (checkout, relatório financeiro, delete user), lógica de pagamento, agregações e logs de auditoria. Não há separação por agregado.
Impact: Qualquer ajuste (ex.: trocar gateway de pagamento) implica editar a mesma classe; impossível testar checkout sem subir DB.
Recommendation: Quebrar em controllers/checkoutController.js, controllers/reportController.js, controllers/userController.js + models/userModel.js, courseModel.js, paymentModel.js, enrollmentModel.js, auditLogModel.js (RP-04).

[CRITICAL] Endpoint DELETE deixa órfãos no DB e nega o problema
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` roda DELETE em users sem tocar enrollments/payments; resposta é "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.".
Impact: Integridade referencial violada por design; relatórios futuros entregam dados inconsistentes; LGPD: dado pessoal não pode ficar amarrado.
Recommendation: Transação que apaga matrículas, pagamentos e usuário em cascata (RP-08); soft-delete se houver requisito legal.

[HIGH] Callback hell aninhado no checkout
File: src/AppManager.js:28-78
Description: 5 níveis de callbacks (course → user → insert enrollment → insert payment → insert audit_log) com `let self = this` para preservar contexto. Tratamento de erro replicado em cada nível.
Impact: Leitura e manutenção difíceis; fácil esquecer um early return; risco de enviar resposta duas vezes.
Recommendation: Promisify db.run/db.get + async/await; controller fica linear (RP-07).

[HIGH] Sem transação no fluxo de checkout
File: src/AppManager.js:50-63
Description: INSERT em enrollments, INSERT em payments e INSERT em audit_logs ocorrem em chamadas independentes; falha no meio deixa dados parciais.
Impact: Cliente cobrado sem enrollment, ou enrollment sem registro de pagamento — inconsistência financeira.
Recommendation: BEGIN/COMMIT explícito no checkout; rollback em qualquer erro (RP-08).

[HIGH] Estado global mutável exportado
File: src/utils.js:9-10, 26
Description: globalCache = {} e totalRevenue = 0 vivem no escopo do módulo e são exportados.
Impact: Race conditions entre requisições; estado vaza entre testes; impossível resetar sem reiniciar o processo.
Recommendation: Cache injetado via DI (Map/Redis); receita derivada de query no momento, não acumulada em memória.

[HIGH] Lógica de pagamento dentro do route handler
File: src/AppManager.js:43-64
Description: Decisão de aprovado/recusado, persistência, log e cache rodam todos dentro do callback da rota.
Impact: Não há service de pagamento reutilizável; bypassar o gateway exige editar a rota; testes só funcionam com app inteiro de pé.
Recommendation: Extrair PaymentService.process(card) → status; CheckoutController orquestra (RP-05).

[MEDIUM] N+1 brutal no relatório financeiro
File: src/AppManager.js:80-129
Description: Para cada curso, listar matrículas; para cada matrícula, fazer query users + query payments. 1 + N_cursos + (N_cursos × M_matriculas × 2).
Impact: Relatório de 10 cursos × 50 matrículas → 1010 queries. Inviável em produção.
Recommendation: Substituir por uma única query SQL com LEFT JOIN entre courses, enrollments, users e payments, agregada em memória (RP-06).

[MEDIUM] Validação de input apenas truthy
File: src/AppManager.js:35
Description: `if (!u || !e || !cid || !cc) return 400`. Não valida formato de email, comprimento de cartão, ou existência de pwd.
Impact: Aceita "x" como nome, "abc" como cartão; quebra mais adiante no fluxo (sem trace).
Recommendation: Esquema com joi/yup/zod validando no middleware ou no controller.

[MEDIUM] Sem middleware de tratamento de erro
File: src/AppManager.js:38, 41, 51, 55, 70 (replicado em cada callback)
Description: Cada callback chama `res.status(500).send("Erro DB")` manualmente; alguns nem retornam após enviar.
Impact: Resposta dupla, falta de log estruturado, fácil esquecer caminhos de erro.
Recommendation: Middleware único `errorHandler(err, req, res, next)` no final da chain; controllers usam `next(err)` (RP-09).

[LOW] Naming abreviado obscuro
File: src/AppManager.js:29-33
Description: `let u = req.body.usr, e = req.body.eml, p = req.body.pwd, cid = req.body.c_id, cc = req.body.card`.
Impact: Leitor não sabe o que cada variável significa; review fica mais lento.
Recommendation: `const { usr: name, eml: email, pwd: password, c_id: courseId, card: creditCard } = req.body` ou renomear o payload na própria API.

[LOW] `let self = this` anti-pattern
File: src/AppManager.js:26
Description: Usa `self = this` em vez de arrow function para preservar contexto em callbacks.
Impact: Idioma legado; confunde junior em revisão; some quando reescreve com async/await.
Recommendation: Arrow functions ou async/await.

[LOW] DEP-004 — express.json + manual em vez de body-parser standalone
File: src/app.js:6
Description: Já usa `app.use(express.json())` (correto desde Express 4.16). Sem violação direta, mas o utils.js sugere expectativa antiga; documentar no playbook.
Impact: Nenhum imediato; nota apenas para manter ciência.
Recommendation: Manter `express.json()` nativo; não trazer body-parser de volta.

[LOW] DEP-005 — sqlite3 com callback-only (legado, não deprecated)
File: package.json:11, src/AppManager.js inteiro
Description: Lib `sqlite3` 5.x usa callbacks; better-sqlite3 ou Prisma seriam mais ergonômicos.
Impact: Estilo só; código fica callback-hell sem promisify.
Recommendation: Manter sqlite3 + promisify (RP-07) ou avaliar migração para better-sqlite3.

================================
Total: 16 findings
================================
```

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
