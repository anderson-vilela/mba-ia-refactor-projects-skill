# Template do Relatório de Auditoria (Fase 2)

Use exatamente este formato. Ele é parseável e fácil de revisar pelo humano. O relatório deve ser impresso no terminal **e** salvo em `reports/audit-report.md` (dentro da raiz do projeto auditado).

## Estrutura

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório raiz>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<M> lines of code
Date:    <YYYY-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

[CRITICAL] <Nome curto do anti-pattern>
File: <caminho/relativo.ext>:<linha>(-<linha-fim>)
Description: <2-3 linhas explicando o que está errado, no contexto deste arquivo>
Impact: <consequência concreta — risco de segurança, perf, manutenção>
Recommendation: <ação concreta de correção>

[CRITICAL] <próximo finding>
File: ...
...

[HIGH] <...>
...

[MEDIUM] <...>
...

[LOW] <...>
...

================================
Total: <N> findings
================================
```

## Regras de formatação

1. **Cabeçalho de findings:** `[SEVERIDADE] Nome do anti-pattern` — sempre em colchetes maiúsculos.
2. **File:** caminho relativo à raiz do projeto, com linhas. Se for um intervalo, use `arquivo.py:10-45`. Se for o arquivo inteiro, use `arquivo.py:1-EOF`.
3. **Description, Impact, Recommendation:** uma sentença por linha, sem markdown rico (sem `**bold**`, sem listas com `-`).
4. **Ordem:** CRITICAL primeiro, depois HIGH, depois MEDIUM, depois LOW. Dentro da mesma severidade, agrupar por arquivo.
5. **Sem duplicação:** se a mesma raiz aparece em 8 linhas do mesmo arquivo, agrupe num finding só com o intervalo.
6. **Cite o número total no final** — soma das severidades.

## Exemplo de finding bem formado

```
[CRITICAL] SQL Injection por concatenação de string
File: models.py:28
Description: Query "SELECT * FROM produtos WHERE id = " + str(id) usa concatenação direta com input externo, mesmo padrão repetido em models.py:47-50, 92, 109-110, 126-128, 140, 155-156.
Impact: Atacante pode injetar SQL arbitrário, exfiltrar usuários/pedidos, dropar tabelas.
Recommendation: Substituir por queries parametrizadas com "?" e tupla de parâmetros, ou migrar para SQLAlchemy.
```

## Exemplo de finding mal formado (NÃO faça)

```
[critical] sql injection
File: models.py
Description: várias queries têm sql injection
Impact: ruim
Recommendation: arruma aí
```

Falhou em: severidade não foi capitalizada, nome do anti-pattern genérico, sem linha, descrição vaga, impacto não específico, recomendação não acionável.

## Salvamento em disco

Após imprimir no terminal, **sempre** salve em `reports/audit-report.md` (dentro do diretório do projeto auditado, não na raiz do monorepo). Crie o diretório se não existir.

Use o `Write` tool para salvar. O conteúdo do arquivo é o mesmo que foi impresso no terminal (incluindo os cabeçalhos `=====`).

## Pergunta final obrigatória

Após salvar o arquivo, imprima literalmente (em linha separada):

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

E espere resposta humana. Não execute a Fase 3 sem `y`/`yes`/`sim`/`s`.

## Tamanho mínimo

- Pelo menos **5 findings** totais.
- Pelo menos **1 CRITICAL ou HIGH**.
- Pelo menos **1 detecção de API deprecated** (seção DEP-*** do catálogo), quando aplicável à stack.

Se os mínimos não forem atingidos, é sinal forte de que a leitura foi superficial. Reanalise.
