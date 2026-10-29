# Estado atual — Small Manufacturing Operations Demo

Revisão documental: 13/10/2026. Nenhum orçamento calculado ou status de pedido alterado.

## Arquitetura observada

`app/main.py` registra saúde, dashboard, pedidos, atualização de status, cotações e auditoria. `app/domain.py` contém `QuoteInputs` e `calculate_quote` com Decimal para trabalho, risco e preço. `app/store.py` usa SQLite e agrega dashboard. Interface em `app/static/` não usa framework de frontend segundo README.

## Regras e limites

[README](../README.md) documenta papéis viewer/operator/admin por header, auditoria de status e dados integralmente sintéticos. O mecanismo é limitado à demo e não representa autenticação de produção. Fórmulas presentes não equivalem a margens ou preços aprovados de operação real; não foram lidos registros do banco.

## Operação e validação

README fornece `python -m uvicorn app.main:app --reload` e `pytest -q`, com documentação API em `/docs`. Todos não executados nesta tarefa. FastAPI, httpx, pydantic, pytest e uvicorn são dependências declaradas. Dockerfile e tests existem; nenhum build ou teste foi executado.

## Retomada

Última etapa comprovada: mapa documental revisado. Sugestões: conferir a regra/fórmula ou transição afetada no código antes de editar; manter dados sintéticos; separar proposta comercial de comportamento da demo. Não há novo roadmap funcional aprovado ou aprendizado fabricado.

[Índice](INDEX.md)
