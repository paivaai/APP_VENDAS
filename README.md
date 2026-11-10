# P-Vendas (PDP — Paiva AI Decision Platform)

SaaS multi-tenant que automatiza a operação de vendedores de marketplace (Mercado Livre, Shopee, TikTok Shop; Shein adiado) com agentes de IA. O cliente aprova as decisões pelo WhatsApp, sem precisar entrar em painel.

**Stack:** FastAPI + PostgreSQL + Next.js 14 + nginx + Docker Compose, na VPS Hostinger em `/opt/pdp/`.

| Serviço | Domínio |
|---|---|
| Frontend (cliente) | pdp.paivaai.com.br |
| API | api.pdp.paivaai.com.br |
| Admin | admin.paivaai.com.br |
| WhatsApp (Evolution API) | evolution.paivaai.com.br |

## App de demonstração (celular)

A pasta `app/` é um app instalável (PWA) com decisões aprovadas por etiqueta ou WhatsApp simulado, status dos canais, teste de cadastro de produto e vendas. Os dados são fictícios e marcados como demonstração. A publicação no GitHub Pages é automática (`.github/workflows/pages.yml`); depois do primeiro deploy, abrir o link no celular e usar "Adicionar à tela inicial".

Rodar localmente: `cd app && python3 -m http.server 8000`.

## Estado

Veja [docs/STATUS.md](docs/STATUS.md) — o que funciona, o que está pendente e o que ainda precisa ser trazido da VPS para este repositório.

## Rodar / publicar na VPS

```bash
cd /opt/pdp
cp .env.example .env      # preencher segredos (nunca commitar o .env)
docker compose up -d --build
```

Depois de qualquer mudança no `nginx/nginx.conf`: `docker restart pdp-nginx-1`.

## Estrutura

```
backend/    FastAPI (auth, integrações, agentes)
app/        App de demonstração (PWA, sem build)
frontend/   Next.js 14 — dashboard do cliente
admin/      Next.js — painel admin (esqueleto)
nginx/      nginx.conf (modelo)
docs/       status, arquitetura e lições de infra
```

## Segurança

- `.env` e chaves **nunca** vão para o Git (ver `.gitignore`); use `.env.example`.
- JWT com expiração de 24h, rate limit de login no nginx, tokens OAuth guardados criptografados (a implementar).
