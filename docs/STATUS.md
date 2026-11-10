# Status do projeto

## Conferido na VPS em 10/nov/2026 (srv1525443)
- Rodando em Docker: `pdp-backend-1` e `pdp-frontend-1` (2 semanas no ar). O nginx é o do **sistema** (`/etc/nginx/sites-enabled/paiva`), não mais um container. O VPS também hospeda farmsat, roadsign-vision e n8n.
- Backend `:8000/docs`, frontend `:3000` e admin `:3001` respondem 200 localmente.
- **Certificado SSL de `pdp.paivaai.com.br` e `api.pdp.paivaai.com.br` venceu em 24/out/2026.** Por isso o acesso público por HTTPS falha. Renovar antes de qualquer apresentação.
- `evolution.paivaai.com.br` não tem registro DNS e não há container da Evolution API rodando.
- `.env` tem ML, TikTok, Bling e Anthropic preenchidos (valores não conferidos). `ML_APP_ID` aparece duplicado. Não há variáveis da Evolution.
- Disco em 73%.
- Arquivos de status antigos na VPS: `INTEGRATION_STATUS.txt`, `DEPLOYMENT_STATUS.txt`, `DEPLOYMENT_REPORT.md`, `MERCADO_LIVRE_INTEGRATION.md`.


Última referência: chats do projeto até 12/ago/2026. **Reconferir na VPS antes de confiar.**

## Funcionando
- Mercado Livre: OAuth completo, testado de ponta a ponta.
- TikTok Shop: conexão direta.
- Infra: pdp / api / admin / evolution no ar (nginx, certbot standalone com hooks, Docker Compose).
- Evolution API: container rodando (banco `evolution` no mesmo Postgres).
- Agentes Pré-venda, Venda, Pós-venda: estrutura criada; Pré-venda parcial (validação + decisão).
- Painel admin: infraestrutura no ar (HTTP 200).

## Pendente / bloqueado
- **Shopee via Bling:** app Bling em "Em desenvolvimento" → FORBIDDEN para contas que não são do dono. Adicionar o cliente como usuário de teste no painel de desenvolvedor do Bling ou concluir a homologação.
- Shein: adiado.
- Mapeamento de categoria por marketplace; chamadas reais de cadastro de produto.
- Fluxo real de aprovação por WhatsApp (3 instâncias por tenant: PRE_SALE, SALE, POST_SALE).
- Admin fase 1: definir se a atividade dos agentes já é registrada em tabela.
- Criptografia dos tokens OAuth, rate limit confirmado no nginx.

## A trazer da VPS para este repo
`backend/app/main.py` completo, integrações ML / TikTok / Shopee, auth (register/login), `nginx.conf` real, `frontend/`, `admin/`, Dockerfiles e `requirements.txt` real.
Os arquivos deste repo são uma **reconstrução** a partir dos chats; os pontos incertos estão marcados com `TODO`.

## Roadmap
1. Destravar Shopee/Bling para o primeiro cliente.
2. Completar Pré-venda (categoria + cadastro real).
3. WhatsApp: aprovação do cliente (Evolution API).
4. Admin: onboarding, atividade dos agentes, cobrança por uso (`ApiUsage`).
5. Segundo cliente.
