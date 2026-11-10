# Status do projeto (P-Vendas / PDP)

Atualizado em 10/nov/2026 a partir da VPS (srv1525443).

## Funcionando
- **App P-Vendas** (pasta `app/`, PWA no GitHub Pages): entrada com Mercado Livre, TikTok Shop, e-mail e senha (e Google, quando o ID de cliente for preenchido). Pedidos reais, sem dados do comprador.
- **Backend real** (`backend/`): FastAPI + PostgreSQL. Entrada social ML/TikTok, cadastro por e-mail, rotas de pedidos, tokens OAuth criptografados (Fernet, chave `TOKEN_ENC_KEY` no `.env`).
- **Infra:** nginx do sistema, certbot com renovação automática (timer ativo), admin protegido por senha em `admin.paivaai.com.br` (porta 3011).

## Pendente
- Confirmação de cadastro por e-mail: falta configurar SMTP (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`). Sem isso a conta nasce confirmada.
- Entrada com Google: criar o ID de cliente no Google Cloud, colocar em `GOOGLE_CLIENT_ID` (`.env`) e em `app/js/app.js`.
- TikTok: teste completo com loja de terceiros (depende do status do app no TikTok Partner).
- Agentes de Venda e Pós-venda e as decisões da aba Hoje ainda não usam dados reais.
- Admin: só o esqueleto do Next.js; falta o painel de clientes.
- WhatsApp (Evolution API): sem DNS, sem container e sem número.
- `backend/requirements.txt` tem pacote inválido (`melipy==1.2.11`): o build da imagem falha. Dependências novas ficam em `backend/_vendor` (fora do Git).
- Política de privacidade e termos.

## Deploy
Os scripts em `deploy/` aplicam as mudanças recentes na VPS (já aplicadas). O código real do backend, frontend e admin está nas pastas `backend/`, `frontend/` e `admin/`. Segredos nunca vão para o Git (`.env*`, `_vendor`, chaves).
