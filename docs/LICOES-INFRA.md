# Lições de infra e código (custaram caro para descobrir)

## nginx / Docker
- `sed -i` troca o inode e quebra arquivo montado por bind-mount. Edite com `cat > arquivo` e use `docker restart pdp-nginx-1` (não só `nginx -s reload`).
- `docker cp` para o container do nginx falha com "device or resource busy"; o arquivo já é o do host (`/opt/pdp/nginx/nginx.conf`, montado `:ro`).
- DNS do Docker: `resolver 127.0.0.11 valid=10s ipv6=off;` + `proxy_pass` via variável + reload automático 15s após subir (já no compose).
- Todos os serviços na mesma rede. O admin isolado em outra rede causou 502.
- O admin deve escutar na mesma porta que o nginx espera (`PORT=3001`).

## Certbot
- Renovação com `standalone` + `pre_hook`/`post_hook` parando e subindo o nginx. Validar com `certbot renew --dry-run`.
- Conferir os caminhos de certificado de cada `server` (já houve certs trocados entre domínios).

## Evolution API
- Precisa de `DATABASE_PROVIDER` e `DATABASE_CONNECTION_URI`; sem eles entra em loop de restart ("Database provider invalid").
- `AUTHENTICATION_API_KEY` deve ser chave real (`openssl rand -hex 32`), nunca placeholder.

## Código
- `os.getenv()` dentro das funções, não no import (retornava `None`).
- O `sub` do JWT é o e-mail; para o OAuth `state` use o UUID do usuário buscado pela tabela.
- Troca de token do Mercado Livre: `api.mercadolibre.com`.
- `.env` único na raiz de `/opt/pdp` (o compose lê esse; `backend/.env` é ignorado).
