#!/usr/bin/env python3
"""Gera a versão com a marca de um cliente (white-label) em app/c/<slug>/.

Uso:
  python3 scripts/novo_cliente.py <slug> --nome "Loja do Guga" --logo logo.png [--cor "#0B7A4B"]

- <slug>: letras minúsculas, números e hífen (vira o endereço: .../APP_VENDAS/c/<slug>/)
- troca nome, logo, ícones do celular, cor principal e a cor da barra do app
- isola cache e login por cliente (várias marcas no mesmo endereço não se misturam)
Depois: git add app/c/<slug> && git commit && git push  (o GitHub Pages publica sozinho)
"""
import argparse, os, re, shutil, sys
from PIL import Image

raiz = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
app = os.path.join(raiz, "app")

ap = argparse.ArgumentParser()
ap.add_argument("slug")
ap.add_argument("--nome", required=True)
ap.add_argument("--logo", required=True, help="PNG ou JPG, de preferência quadrado e com fundo transparente")
ap.add_argument("--cor", default="#2B59FF", help="cor principal em hexadecimal")
a = ap.parse_args()

if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,39}", a.slug):
    sys.exit("slug inválido: use minúsculas, números e hífen")
if not re.fullmatch(r"#[0-9a-fA-F]{6}", a.cor):
    sys.exit("cor inválida: use o formato #RRGGBB")
if "<" in a.nome or '"' in a.nome or len(a.nome) > 40:
    sys.exit("nome inválido (até 40 caracteres, sem aspas nem <)")
nome = a.nome.strip()

dest = os.path.join(app, "c", a.slug)
if os.path.exists(dest):
    shutil.rmtree(dest)
shutil.copytree(app, dest, ignore=shutil.ignore_patterns("c"))


def ler(p):
    return open(os.path.join(dest, p), encoding="utf-8").read()


def gravar(p, s):
    open(os.path.join(dest, p), "w", encoding="utf-8").write(s)


# logo e ícones
logo = Image.open(a.logo).convert("RGBA")
logo.thumbnail((256, 256))
logo.save(os.path.join(dest, "icons", "logo.png"))
hexa = a.cor.lstrip("#")
fundo = tuple(int(hexa[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def icone(tam, margem, nome_arq):
    img = Image.new("RGBA", (tam, tam), fundo)
    lado = int(tam * (1 - 2 * margem))
    l = logo.copy(); l.thumbnail((lado, lado))
    img.paste(l, ((tam - l.width) // 2, (tam - l.height) // 2), l)
    img.convert("RGB").save(os.path.join(dest, "icons", nome_arq))


icone(192, 0.15, "icon-192.png")
icone(512, 0.15, "icon-512.png")
icone(512, 0.25, "icon-maskable-512.png")

# página
h = ler("index.html")
h = h.replace("Pré-venda Paiva", "Pré-venda").replace("P-Vendas", nome).replace("icons/logo.svg", "icons/logo.png")
h = h.replace('<meta name="theme-color" content="#162033">', '<meta name="theme-color" content="%s">' % a.cor)
gravar("index.html", h)

# script: textos e armazenamento separados por cliente
j = ler("js/app.js")
j = j.replace('const MARCA = "";', 'const MARCA = "%s";' % a.slug).replace("Pré-venda Paiva", "Pré-venda").replace("Venda Paiva", "Venda").replace('"pdp-demo-v1"', '"pv-%s-demo"' % a.slug).replace('"pdp-token"', '"pv-%s-token"' % a.slug)
gravar("js/app.js", j)

# estilo
c = ler("css/app.css")
c = c.replace("--tape:#2B59FF;", "--tape:%s;" % a.cor)
gravar("css/app.css", c)

# manifesto
m = ler("manifest.webmanifest")
m = m.replace('"P-Vendas"', '"%s"' % nome).replace('"#162033"', '"%s"' % a.cor)
gravar("manifest.webmanifest", m)

# service worker: cache próprio e logo em PNG
sw = ler("service-worker.js")
sw = sw.replace("'paiva-ai-'", "'pv-%s-'" % a.slug).replace("icons/logo.svg", "icons/logo.png")
gravar("service-worker.js", sw)

os.remove(os.path.join(dest, "icons", "logo.svg")) if os.path.exists(os.path.join(dest, "icons", "logo.svg")) else None
print("pronto: app/c/%s  ->  https://paivaai.github.io/APP_VENDAS/c/%s/" % (a.slug, a.slug))
