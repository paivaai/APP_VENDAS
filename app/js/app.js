// P-Vendas
(function () {
  "use strict";

  /* ---------- utilidades ---------- */
  const $ = (s, r) => (r || document).querySelector(s);
  const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
  const brl2 = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
  const KEY = "pdp-demo-v1";

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; }
  }
  function save(s) {
    try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) { /* sem armazenamento: segue em memória */ }
  }
  let decided = load(); // { id: { opt, via, at } }

  function el(tag, attrs, children) {
    const n = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([k, v]) => {
      if (k === "class") n.className = v;
      else if (k === "text") n.textContent = v;
      else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v);
    });
    (children || []).forEach((c) => n.append(c));
    return n;
  }

  /* ---------- decisões (dados de demonstração) ---------- */
  const DECISIONS = [
    {
      id: "d1", channel: "Mercado Livre", crit: "critica", waiting: "esperando há 26 h",
      title: "Cliente recebeu a caixa amassada e pede devolução",
      detail: "Pedido de R$ 164. O cliente enviou fotos e abriu reclamação, o que afeta a reputação da loja.",
      options: [
        { k: "A", label: "Aceitar a devolução e reenviar", effect: "Custa o frete de envio e de volta, cerca de R$ 38. Protege a reputação.", value: 164 },
        { k: "B", label: "Oferecer reembolso parcial de 30%", effect: "Custa R$ 49 e o cliente fica com o produto. Pode não encerrar a reclamação.", value: 85 }
      ],
      more: "Nas últimas 20 reclamações parecidas, 14 foram encerradas com a troca. A reclamação aberta pesa mais na reputação do que o custo do frete."
    },
    {
      id: "d2", channel: "Mercado Livre", crit: "alta", waiting: "esperando há 5 h",
      title: "Sérum facial 30 ml vai acabar em 1 dia",
      detail: "Restam 4 unidades e a loja vende cerca de 3 por dia. A reposição leva 6 dias.",
      options: [
        { k: "A", label: "Pausar o anúncio até repor", effect: "Evita cancelar pedido por falta de estoque. Deixa de vender cerca de R$ 280.", value: 210 },
        { k: "B", label: "Manter ativo e subir o preço em 8%", effect: "As últimas unidades saem com mais margem, em ritmo mais lento.", value: 95 }
      ],
      more: "O anúncio é o segundo que mais vende da loja. Pausar não tira a posição dele na busca por até 7 dias."
    },
    {
      id: "d3", channel: "TikTok Shop", crit: "normal", waiting: "esperando há 40 min",
      title: "Cliente pediu cupom de 10% num pedido de R$ 189",
      detail: "É a segunda compra dela este ano. A margem deste produto é de 32%.",
      options: [
        { k: "A", label: "Aprovar o cupom de 10%", effect: "A margem cai de 32% para 24% neste pedido. Clientes recorrentes voltam mais.", value: 120 },
        { k: "B", label: "Oferecer frete grátis no lugar", effect: "Custa R$ 18 e a margem fica em 27%.", value: 150 }
      ],
      more: "Quem recebeu frete grátis em vez de desconto voltou a comprar em 30 dias na mesma proporção, com margem maior."
    }
  ];

  const CRIT = { normal: "Prioridade normal", alta: "Prioridade alta", critica: "Prioridade crítica" };

  /* ---------- aba Hoje ---------- */
  function greet() {
    const h = new Date().getHours();
    return (h < 12 ? "Bom dia" : h < 18 ? "Boa tarde" : "Boa noite") + ", Loja Demo";
  }

  function renderHoje() {
    $("#saudacao").textContent = greet();
    const pend = DECISIONS.filter((d) => !decided[d.id]);
    const done = DECISIONS.filter((d) => decided[d.id]);

    $("#h-hoje").textContent =
      pend.length === 0 ? "Tudo decidido por agora"
      : pend.length === 1 ? "1 decisão espera você"
      : pend.length + " decisões esperam você";

    const badge = $("#badge");
    badge.textContent = pend.length;
    badge.hidden = pend.length === 0;

    const total = done.reduce((s, d) => s + d.options.find((o) => o.k === decided[d.id].opt).value, 0);
    $("#roi-valor").textContent = brl.format(total);

    const box = $("#slips");
    box.replaceChildren();
    if (!pend.length) {
      box.append(el("div", { class: "empty" }, [
        el("strong", { text: "Nada pendente." }),
        el("span", { text: "Quando um agente encontrar algo para decidir, a etiqueta aparece aqui e no seu WhatsApp." })
      ]));
    }
    pend.forEach((d) => box.append(slip(d)));

    $("#t-feitas").hidden = done.length === 0;
    const ul = $("#feitas");
    ul.replaceChildren();
    done.sort((a, b) => decided[b.id].at - decided[a.id].at).forEach((d) => {
      const o = d.options.find((x) => x.k === decided[d.id].opt);
      ul.append(el("li", {}, [
        el("span", { class: "done-title", text: d.title }),
        el("span", { class: "done-sub", text: "Opção " + o.k + ": " + o.label + ". Decidido " + (decided[d.id].via === "WhatsApp" ? "pelo WhatsApp" : "no app") + "." }),
        el("button", { class: "linkbtn", text: "Reverter", onclick: () => undo(d.id) })
      ]));
    });
  }

  function slip(d) {
    const opts = d.options.map((o) =>
      el("div", { class: "opt" }, [
        el("span", { class: "opt-key", text: o.k, "aria-hidden": "true" }),
        el("span", { class: "opt-name", text: o.label }),
        el("span", { class: "opt-effect", text: o.effect }),
        el("button", { class: "btn btn-primary opt-go", text: "Aprovar opção " + o.k, onclick: (e) => choose(d.id, o.k, "app", e.currentTarget.closest(".slip")) })
      ])
    );
    return el("article", { class: "slip", "data-crit": d.crit }, [
      el("div", { class: "slip-top" }, [
        el("div", { class: "slip-meta" }, [
          el("strong", { text: d.channel }),
          el("span", { class: "slip-crit", text: CRIT[d.crit] + ", " + d.waiting })
        ]),
        el("h3", { text: d.title }),
        el("p", { text: d.detail })
      ]),
      el("div", { class: "slip-perf", "aria-hidden": "true" }),
      el("div", { class: "slip-opts" }, opts),
      el("div", { class: "slip-actions" }, [
        el("button", { class: "btn btn-line btn-wide", text: "Responder pelo WhatsApp", onclick: () => openDecisionChat(d) })
      ])
    ]);
  }

  /* ---------- decidir e desfazer ---------- */
  let toastTimer = null;
  function choose(id, opt, via, node) {
    const dd = DECISIONS.find((x) => x.id === id);
    if (dd && dd.draft && opt === "A") { try { navigator.clipboard.writeText(dd.draft); } catch (e) { /* sem área de transferência */ } }
    const finish = () => {
      decided[id] = { opt: opt, via: via, at: Date.now() };
      save(decided);
      renderHoje();
      const d = DECISIONS.find((x) => x.id === id);
      showToast(d.draft && opt === "A" ? "Resposta copiada. Cole na pergunta, dentro do Mercado Livre." : "Opção " + opt + " aprovada: " + d.title, id);
    };
    if (node && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
      node.classList.add("leaving");
      setTimeout(finish, 280);
    } else finish();
  }
  function undo(id) {
    delete decided[id];
    save(decided);
    hideToast();
    renderHoje();
  }
  function showToast(text, id) {
    $("#toast-text").textContent = text;
    const b = $("#toast-undo");
    b.onclick = () => undo(id);
    $("#toast").hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(hideToast, 6500);
  }
  function hideToast() { $("#toast").hidden = true; }

  /* ---------- conversa de WhatsApp (simulada) ---------- */
  const sheet = $("#sheet");
  function bubble(kind, lines) {
    const b = el("div", { class: "bub " + kind });
    lines.forEach((ln, i) => {
      if (i) b.append("\n");
      if (ln.b) b.append(el("b", { text: ln.t })); else b.append(ln.t);
    });
    return b;
  }
  function openSheet(title, bubbles, replies) {
    $("#sheet-title").textContent = title;
    const chat = $("#chat");
    chat.replaceChildren(...bubbles);
    const rep = $("#chat-reply");
    rep.replaceChildren(...replies);
    if (!sheet.open) sheet.showModal();
  }
  $("#sheet-close").addEventListener("click", () => sheet.close());
  sheet.addEventListener("click", (e) => { if (e.target === sheet) sheet.close(); });

  function openDecisionChat(d) {
    const A = d.options[0], B = d.options[1];
    const chat = $("#chat");
    const msg = bubble("in", [
      { t: "Decisão da " + (d.channel === "TikTok Shop" ? "venda" : "pré-venda") + " em " + d.channel, b: true },
      { t: d.title, b: true },
      { t: d.detail },
      { t: "" },
      { t: "1  " + A.label, b: true }, { t: A.effect },
      { t: "" },
      { t: "2  " + B.label, b: true }, { t: B.effect },
      { t: "" },
      { t: "3  Quero mais detalhes", b: true }
    ]);
    const reply = (label, fn) => el("button", { class: "chip", text: label, onclick: fn });
    const lock = () => $("#chat-reply").querySelectorAll("button").forEach((b) => (b.disabled = true));
    const answer = (n, k) => {
      chat.append(bubble("out", [{ t: String(n) }]));
      lock();
      setTimeout(() => {
        chat.append(bubble("in", [{ t: "Combinado. Registrei a opção " + k + " e já atualizei o painel. Você pode reverter por lá quando quiser." }]));
        choose(d.id, k, "WhatsApp");
        setTimeout(() => sheet.close(), 1400);
      }, 600);
    };
    openSheet(d.channel === "TikTok Shop" ? "Venda Paiva" : "Pré-venda Paiva", [msg], [
      reply("1", () => answer(1, "A")),
      reply("2", () => answer(2, "B")),
      reply("3", (e) => {
        chat.append(bubble("out", [{ t: "3" }]));
        e.currentTarget.disabled = true;
        setTimeout(() => chat.append(bubble("in", [{ t: d.more }])), 500);
      })
    ]);
  }

  /* ---------- aba Agentes: validar produto ---------- */
  const REQUIRED = {
    mercado_livre: ["title", "description", "price", "sku", "stock", "category_hint"],
    shopee: ["title", "description", "price", "sku", "stock"],
    shein: ["title", "description", "price", "sku", "stock", "images"],
    tiktok: ["title", "description", "price", "sku", "stock", "images"]
  };
  const LABEL = { title: "Título", description: "Descrição", price: "Preço", sku: "SKU", stock: "Estoque", category_hint: "Categoria sugerida", images: "Imagens" };
  const MKT = { mercado_livre: "Mercado Livre", shopee: "Shopee", shein: "Shein", tiktok: "TikTok Shop" };

  /* fotos do produto: ficam só neste aparelho, nesta demonstração */
  let fotos = [];
  function pintarFotos() {
    const box = $("#f-prev"); box.replaceChildren();
    fotos.forEach((f, i) => {
      const img = el("img", { alt: "Foto " + (i + 1) });
      img.src = f.url;
      box.append(el("div", { class: "ph" }, [img, el("button", { type: "button", "aria-label": "Remover foto " + (i + 1), text: "×", onclick: () => { URL.revokeObjectURL(f.url); fotos.splice(i, 1); pintarFotos(); } })]));
    });
    $("#f-images").value = String(fotos.length);
    $("#f-fotos-n").textContent = fotos.length ? fotos.length + (fotos.length === 1 ? " foto adicionada." : " fotos adicionadas.") + " Mínimo recomendado: 3." : "Nenhuma foto ainda. Use fotos nítidas, com fundo claro.";
  }
  $("#f-fotos-btn").addEventListener("click", () => $("#f-fotos").click());
  $("#f-fotos").addEventListener("change", (e) => {
    Array.from(e.target.files || []).slice(0, 12 - fotos.length).forEach((f) => { if (f.type.startsWith("image/")) fotos.push({ url: URL.createObjectURL(f) }); });
    e.target.value = ""; pintarFotos();
  });

  $("#form-produto").addEventListener("submit", (e) => {
    e.preventDefault();
    const mkt = $("#f-mkt").value;
    const row = {};
    Object.keys(LABEL).forEach((f) => { row[f] = ($("#f-" + f).value || "").trim(); });
    const missing = REQUIRED[mkt].filter((f) => !row[f]);
    const box = $("#resultado");
    box.hidden = false;
    box.replaceChildren();
    box.className = "resultado" + (missing.length ? " falta" : "");
    if (!missing.length) {
      box.append(
        el("h3", { text: "Pronto para cadastrar no " + MKT[mkt] }),
        el("p", { text: "Todos os campos exigidos estão preenchidos. O agente marca o produto como pronto e cadastra sem precisar de você." })
      );
      return;
    }
    const ul = el("ul", {}, missing.map((f) => el("li", { text: LABEL[f] })));
    box.append(
      el("h3", { text: "Faltam " + missing.length + (missing.length === 1 ? " campo" : " campos") + " para o " + MKT[mkt] }),
      ul,
      el("p", { text: "O agente guarda o produto como pendente e pede os dados ao lojista pelo WhatsApp." }),
      el("button", {
        class: "btn btn-line", type: "button", text: "Ver a mensagem enviada",
        onclick: () => {
          const name = row.title || "seu produto";
          const lines = [{ t: "Pré-venda Paiva", b: true }, { t: "Vou cadastrar " + name + " no " + MKT[mkt] + ", mas faltam estes dados:" }, { t: "" }]
            .concat(missing.map((f) => ({ t: "- " + LABEL[f] })))
            .concat([{ t: "" }, { t: "É só responder aqui com as informações." }]);
          openSheet("Pré-venda Paiva", [bubble("in", lines)], [el("button", { class: "chip", text: "Fechar", onclick: () => sheet.close() })]);
        }
      })
    );
  });

  /* ---------- aba Canais ---------- */
  const CANAIS = [
    { n: "Mercado Livre", s: "Conectado", t: "ok", note: "Login autorizado testado de ponta a ponta. Lê pedidos, produtos e métricas." },
    { n: "TikTok Shop", s: "Conectado só para leitura", t: "ok", note: "Falta pedir a permissão de escrita para cadastrar e alterar produtos." },
    { n: "WhatsApp", s: "Em configuração", t: "warn", note: "O servidor está instalado. Faltam as 3 conversas por loja: pré-venda, venda e pós-venda." },
    { n: "Claude, a IA dos agentes", s: "Ativo", t: "ok", note: "Modelo rápido para a rotina e modelo avançado para decisões difíceis. O consumo é registrado por loja." },
    { n: "Shein", s: "Planejado", t: "off", note: "Entra depois que Mercado Livre e TikTok Shop estiverem estáveis." }
  ];
  function renderCanais() {
    const ul = $("#canais");
    ul.replaceChildren();
    CANAIS.forEach((c) => ul.append(el("li", {}, [
      el("span", { class: "dot " + c.t, "aria-hidden": "true" }),
      el("div", {}, [el("div", { class: "ch-name", text: c.n }), el("div", { class: "ch-status " + c.t, text: c.s })]),
      el("p", { class: "ch-note", text: c.note })
    ].concat(c.link ? [el("button", { class: "btn " + (c.on ? "btn-line" : "btn-primary") + " ch-btn", type: "button", text: c.on ? "Adicionar outra loja" : "Conectar " + c.n, onclick: () => ligar(c.link) })] : []))));
  }

  /* ---------- aba Loja (números fictícios, sempre iguais) ---------- */
  function rng(seed) { let s = seed; return () => ((s = (s * 16807) % 2147483647) / 2147483647); }
  const CH = [
    { id: "total", n: "Total" }, { id: "ml", n: "Mercado Livre", seed: 11, base: 1500 },
    { id: "tt", n: "TikTok Shop", seed: 23, base: 900 }
  ];
  const DIAS = ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"];
  function serie(c) {
    const r = rng(c.seed), out = [];
    for (let i = 0; i < 7; i++) out.push(Math.round(c.base * (0.65 + r() * 0.7)));
    return out;
  }
  const SERIES = {};
  CH.slice(1).forEach((c) => (SERIES[c.id] = serie(c)));
  SERIES.total = SERIES.ml.map((v, i) => v + SERIES.tt[i]);
  const PEDIDOS = [
    ["Sérum facial 30 ml", "Camila R.", 89.9, "há 12 min"], ["Kit hidratante 3 itens", "Rafael M.", 164, "há 1 h"],
    ["Protetor solar FPS 50", "Juliana P.", 59.9, "há 2 h"], ["Máscara capilar 300 g", "Bruno S.", 74.5, "há 3 h"],
    ["Shampoo sem sulfato", "Aline T.", 48, "há 5 h"]
  ];
  let canalAtual = "total";
  function renderLoja() {
    const seg = $("#seg");
    seg.replaceChildren();
    CH.forEach((c) => seg.append(el("button", {
      role: "tab", text: c.n, "aria-selected": String(c.id === canalAtual),
      onclick: () => { canalAtual = c.id; renderLoja(); }
    })));
    const s = SERIES[canalAtual];
    const fat = s.reduce((a, b) => a + b, 0);
    const ped = Math.round(fat / 96);
    $("#figuras").replaceChildren(
      fig(brl.format(fat), "faturamento em 7 dias"),
      fig(String(ped), "pedidos"),
      fig(brl.format(Math.round(fat / ped)), "ticket médio")
    );
    const max = Math.max(...s);
    const hoje = new Date().getDay();
    const bars = $("#barras");
    bars.replaceChildren();
    s.forEach((v, i) => {
      const d = DIAS[(hoje - (6 - i) + 14) % 7];
      const b = el("div", { class: "bar", title: brl.format(v) }, [el("span", { text: d })]);
      b.style.height = Math.round((v / max) * 100) + "%";
      bars.append(b);
    });
    const ul = $("#pedidos");
    ul.replaceChildren();
    PEDIDOS.forEach((p) => ul.append(el("li", {}, [
      el("span", { class: "o-name", text: p[0] }),
      el("span", { class: "o-sub", text: p[1] + ", " + p[3] }),
      el("span", { class: "o-val", text: brl2.format(p[2]) })
    ])));
  }
  function fig(num, lab) {
    return el("div", { class: "fig" }, [el("div", { class: "fig-num", text: num }), el("div", { class: "fig-lab", text: lab })]);
  }

  /* ---------- navegação ---------- */
  document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => {
    const v = t.dataset.view;
    document.querySelectorAll(".view").forEach((s) => (s.hidden = s.id !== "view-" + v));
    document.querySelectorAll(".tab").forEach((x) => {
      const on = x === t;
      x.classList.toggle("is-active", on);
      if (on) x.setAttribute("aria-current", "page"); else x.removeAttribute("aria-current");
    });
    window.scrollTo(0, 0);
  }));

  renderHoje();
  renderCanais();
  renderLoja();

  /* ---------- entrar com a conta do marketplace (dados reais) ---------- */
  const API = "https://api.pdp.paivaai.com.br";
  const TK = "pdp-token";
  const MARCA = ""; // preenchido pelo gerador de marca (white-label); vazio no app principal
  const via = (destino) => (MARCA ? API + "/auth/marca?r=" + MARCA + "&to=" + encodeURIComponent(destino) : destino);
  const lerToken = () => { try { return localStorage.getItem(TK); } catch (e) { return null; } };
  const gravarToken = (t) => { try { if (t) localStorage.setItem(TK, t); else localStorage.removeItem(TK); } catch (e) { /* sem armazenamento */ } };

  // o servidor devolve o token no fragmento (#token=...), que nunca vai para nenhum servidor
  let tokenMem = null;
  const m = /[#&]token=([^&]+)/.exec(location.hash);
  if (m) { tokenMem = decodeURIComponent(m[1]); gravarToken(tokenMem); history.replaceState(null, "", location.pathname + location.search); }
  const token = () => tokenMem || lerToken();
  let aviso = "";
  const hv = /[#&](verificado|conectado)=([^&]+)/.exec(location.hash);
  if (hv) {
    aviso = hv[1] === "verificado" ? (hv[2] === "1" ? "E-mail confirmado! Agora entre com o seu e-mail e a senha." : "Este link de confirmação não é válido ou já foi usado.") : "Canal conectado com sucesso.";
    history.replaceState(null, "", location.pathname + location.search);
  }

  async function api(caminho, opts) {
    const o = opts || {};
    const r = await fetch(API + caminho, { method: o.method || "GET", headers: Object.assign({ Authorization: "Bearer " + token() }, o.body ? { "Content-Type": "application/json" } : {}), body: o.body ? JSON.stringify(o.body) : undefined });
    if (r.status === 401) { const e = new Error("sessao"); e.sessao = true; throw e; }
    if (!r.ok) throw new Error("http " + r.status);
    return r.json();
  }

  function mostrarLogin(msg) {
    $("#login").hidden = false;
    $("#login-msg").textContent = msg || "";
  }
  $("#login-tiktok").addEventListener("click", () => { location.href = via(API + "/integrations/tiktok/login"); });
  $("#login-ml").addEventListener("click", () => { location.href = via(API + "/integrations/mercadolivre/login"); });
  $("#login-demo").addEventListener("click", () => { $("#login").hidden = true; });

  // Entrar com Google: preencha o ID do cliente (público) criado no Google Cloud e o botão aparece
  const GOOGLE_CLIENT_ID = "839252003508-r3q6vg12rejgqg8a3541oa8935fe0nam.apps.googleusercontent.com";
  function iniciarGoogle() {
    if (!GOOGLE_CLIENT_ID) return;
    const s = document.createElement("script"); s.src = "https://accounts.google.com/gsi/client"; s.async = true;
    s.onload = () => {
      if (!window.google || !google.accounts) return;
      google.accounts.id.initialize({ client_id: GOOGLE_CLIENT_ID, callback: async (resp) => {
        $("#login-msg").textContent = "Entrando com Google…";
        try {
          const r = await fetch(API + "/auth/google", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ credential: resp.credential }) });
          const d = await r.json().catch(() => ({}));
          if (!r.ok) { $("#login-msg").textContent = typeof d.detail === "string" ? d.detail : "Não foi possível entrar com o Google."; return; }
          entrarComToken(d.access_token, d.name);
        } catch (e) { $("#login-msg").textContent = "Sem conexão com o servidor. Tente de novo."; }
      } });
      const box = $("#g-btn"); box.hidden = false;
      google.accounts.id.renderButton(box, { theme: "outline", size: "large", text: "signin_with", shape: "rectangular", locale: "pt-BR", width: 300 });
    };
    document.head.append(s);
  }

  let modo = "entrar";
  document.querySelectorAll("#modo-conta button").forEach((b) => b.addEventListener("click", () => {
    modo = b.dataset.m;
    document.querySelectorAll("#modo-conta button").forEach((x) => x.setAttribute("aria-selected", String(x === b)));
    $("#l-nome").hidden = modo !== "criar";
    $("#c-ok").textContent = modo === "criar" ? "Criar minha conta" : "Entrar";
    $("#c-senha").autocomplete = modo === "criar" ? "new-password" : "current-password";
    $("#login-msg").textContent = "";
  }));
  function entrarComToken(t, nome) {
    gravarToken(t); tokenMem = t; $("#login").hidden = true; if (nome) nomeConta = nome; iniciarReal();
  }
  let nomeConta = "";
  $("#form-conta").addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = $("#login-msg"), btn = $("#c-ok");
    const email = $("#c-email").value.trim(), senha = $("#c-senha").value, nome = $("#c-nome").value.trim();
    if (!email || !senha || (modo === "criar" && !nome)) { msg.textContent = "Preencha todos os campos."; return; }
    btn.disabled = true; msg.textContent = "Um instante…";
    try {
      const r = await fetch(API + (modo === "criar" ? "/auth/signup" : "/auth/entrar"), { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(modo === "criar" ? { name: nome, email, password: senha } : { email, password: senha }) });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { msg.textContent = typeof d.detail === "string" ? d.detail : "Confira os dados e tente de novo."; return; }
      if (d.verificacao === "email") { msg.textContent = "Enviamos um e-mail para " + email + ". Abra a mensagem, toque em confirmar e volte aqui para entrar."; return; }
      if (d.access_token) entrarComToken(d.access_token, d.name);
    } catch (err) { msg.textContent = "Sem conexão com o servidor. Tente de novo."; }
    finally { btn.disabled = false; }
  });

  // nenhum dado pessoal do comprador é buscado nem mostrado: só id curto, status, valor e hora
  let lojaFiltro = "todas";
  function renderLojaReal(todos) {
    const nomeLoja = (o) => o.store || o.channel || "Loja";
    const lojas = Array.from(new Set(todos.map(nomeLoja)));
    if (lojaFiltro !== "todas" && !lojas.includes(lojaFiltro)) lojaFiltro = "todas";
    const pedidos = lojaFiltro === "todas" ? todos : todos.filter((o) => nomeLoja(o) === lojaFiltro);
    const seg = $("#seg"); seg.replaceChildren();
    if (lojas.length > 1) ["todas"].concat(lojas).forEach((n) => seg.append(el("button", {
      role: "tab", text: n === "todas" ? "Todas as lojas" : n, "aria-selected": String(n === lojaFiltro),
      onclick: () => { lojaFiltro = n; renderLojaReal(todos); }
    })));
    const hoje = new Date(); hoje.setHours(0, 0, 0, 0);
    const dias = Array(7).fill(0), qtd = Array(7).fill(0);
    pedidos.forEach((o) => {
      const d = new Date(String(o.created_at).replace(" ", "T")); d.setHours(0, 0, 0, 0);
      const i = 6 - Math.round((hoje - d) / 86400000);
      if (i >= 0 && i < 7) { dias[i] += Number(o.total || 0); qtd[i]++; }
    });
    const fat = dias.reduce((a, b) => a + b, 0), n = qtd.reduce((a, b) => a + b, 0);
    $("#figuras").replaceChildren(fig(brl.format(fat), "faturamento em 7 dias"), fig(String(n), "pedidos em 7 dias"), fig(n ? brl.format(Math.round(fat / n)) : "R$ 0", "ticket médio"));
    const max = Math.max(1, ...dias), bars = $("#barras"); bars.replaceChildren();
    dias.forEach((v, i) => {
      const d = DIAS[(hoje.getDay() - (6 - i) + 14) % 7];
      const b = el("div", { class: "bar", title: brl.format(v) }, [el("span", { text: d })]);
      b.style.height = Math.max(3, Math.round((v / max) * 100)) + "%"; bars.append(b);
    });
    const ul = $("#pedidos"); ul.replaceChildren();
    if (!pedidos.length) ul.append(el("li", { class: "vazio" }, [el("span", { class: "o-name", text: "Nenhum pedido nos últimos dias" }), el("span", { class: "o-sub", text: "A conta está conectada e lida com sucesso. Quando houver vendas, elas aparecem aqui." })]));
    pedidos.slice(0, 8).forEach((o) => ul.append(el("li", {}, [
      el("span", { class: "o-name", text: "Pedido ···" + String(o.order_id || o.tiktok_order_id || o.id).slice(-4) }),
      el("span", { class: "o-sub", text: (o.channel || "") + " · " + (o.status || "sem status").toLowerCase().replace(/_/g, " ") }),
      el("span", { class: "o-val", text: brl2.format(Number(o.total || 0)) })
    ])));
    $("#h-loja").textContent = "Vendas da sua loja";
    $("#view-loja .lead-text").textContent = "Pedidos reais da sua conta. Nomes e dados dos compradores não aparecem aqui.";
  }

  $("#sair").addEventListener("click", () => { gravarToken(null); tokenMem = null; location.reload(); });

  async function ligar(caminho) {
    try { const d = await api(caminho); location.href = via(d.auth_url); }
    catch (e) { if (e.sessao) { gravarToken(null); tokenMem = null; mostrarLogin("Sua sessão expirou. Entre de novo."); } }
  }
  function irParaCanais() { const t = document.querySelector('.tab[data-view="canais"]'); if (t) t.click(); }

  /* ---------- agentes: decisões geradas a partir dos pedidos reais (só leitura) ---------- */
  function gerarDecisoes(pedidos, canaisTxt) {
    const dia = 86400000, agora = Date.now();
    const dt = (o) => new Date(String(o.created_at).replace(" ", "T")).getTime();
    const v = (o) => Number(o.total || 0);
    const sem1 = pedidos.filter((o) => agora - dt(o) <= 7 * dia);
    const sem0 = pedidos.filter((o) => agora - dt(o) > 7 * dia && agora - dt(o) <= 14 * dia);
    const cancel = sem1.filter((o) => /cancel|invalid|return|refund/i.test(String(o.status)));
    const pend = pedidos.filter((o) => /unpaid|payment_required|payment_in_process|pending/i.test(String(o.status)) && agora - dt(o) > dia);
    const ok1 = sem1.filter((o) => !cancel.includes(o));
    const fat1 = ok1.reduce((a, o) => a + v(o), 0), fat0 = sem0.reduce((a, o) => a + v(o), 0);
    const semana = new Date().toISOString().slice(0, 10);
    const base = { channel: canaisTxt, waiting: "análise de agora" };
    const out = [];
    if (cancel.length) {
      const t = cancel.reduce((a, o) => a + v(o), 0);
      out.push(Object.assign({}, base, { id: "r-cancel-" + semana, crit: "alta",
        title: cancel.length + (cancel.length === 1 ? " pedido cancelado" : " pedidos cancelados") + " nos últimos 7 dias",
        detail: "Somam " + brl.format(t) + ". Cancelamentos e devoluções pesam na reputação da loja.",
        options: [
          { k: "A", label: "Revisar os motivos e falar com os compradores", effect: "O agente separa os pedidos e prepara a mensagem de contato para você aprovar.", value: Math.round(t * 0.4) },
          { k: "B", label: "Só acompanhar por mais uma semana", effect: "Não muda nada agora. Se subir, o agente avisa de novo.", value: 0 }],
        more: "Pedidos afetados: " + cancel.slice(0, 5).map((o) => "···" + String(o.order_id || o.id).slice(-4)).join(", ") + ". Dados do comprador não são lidos." }));
    }
    if (pend.length) {
      const t = pend.reduce((a, o) => a + v(o), 0);
      out.push(Object.assign({}, base, { id: "r-pend-" + semana, crit: "normal", waiting: "há mais de 24 h",
        title: pend.length + (pend.length === 1 ? " pedido" : " pedidos") + " sem pagamento confirmado",
        detail: "Somam " + brl.format(t) + " e estão parados há mais de um dia.",
        options: [
          { k: "A", label: "Enviar um lembrete de pagamento", effect: "O agente prepara a mensagem. Você aprova antes de sair.", value: Math.round(t * 0.35) },
          { k: "B", label: "Deixar expirar sozinho", effect: "Sem custo, mas o estoque fica reservado até expirar.", value: 0 }],
        more: "Lembretes costumam recuperar parte desses pedidos quando enviados no mesmo dia." }));
    }
    if (fat0 > 0 && fat1 < fat0 * 0.8) {
      const q = Math.round((1 - fat1 / fat0) * 100);
      out.push(Object.assign({}, base, { id: "r-queda-" + semana, crit: "alta",
        title: "As vendas caíram " + q + "% contra a semana anterior",
        detail: "Esta semana: " + brl.format(fat1) + ". Semana anterior: " + brl.format(fat0) + ".",
        options: [
          { k: "A", label: "Revisar preço e título dos anúncios que mais vendiam", effect: "O agente lista os anúncios para você ajustar.", value: Math.round(fat0 - fat1) },
          { k: "B", label: "Esperar mais uma semana", effect: "Vendas oscilam. Se continuar caindo, o agente avisa.", value: 0 }],
        more: "A comparação usa os pedidos lidos agora das suas contas conectadas." }));
    } else if (fat1 > 0) {
      const por = {};
      ok1.forEach((o) => { const d = DIAS[new Date(dt(o)).getDay()]; por[d] = (por[d] || 0) + v(o); });
      const top = Object.entries(por).sort((a, b) => b[1] - a[1])[0];
      out.push(Object.assign({}, base, { id: "r-forte-" + semana, crit: "normal",
        title: "Seu melhor dia foi " + top[0] + ", com " + brl.format(top[1]),
        detail: "Em 7 dias a loja faturou " + brl.format(fat1) + " em " + ok1.length + (ok1.length === 1 ? " pedido." : " pedidos."),
        options: [
          { k: "A", label: "Reforçar anúncios e cupom nesse dia da semana", effect: "O agente sugere o cupom. Nada é criado sem a sua aprovação.", value: Math.round(top[1] * 0.1) },
          { k: "B", label: "Manter como está", effect: "Sem mudança.", value: 0 }],
        more: "Dia mais forte calculado só com os pedidos concluídos dos últimos 7 dias." }));
    }
    if (!out.length) {
      out.push(Object.assign({}, base, { id: "r-vazio-" + semana, crit: "normal",
        title: "Sem vendas nos últimos 7 dias",
        detail: "A conta está conectada e lida com sucesso, mas não há pedidos recentes.",
        options: [
          { k: "A", label: "Revisar preço e fotos dos anúncios", effect: "O agente lista os anúncios sem venda para você revisar.", value: 0 },
          { k: "B", label: "Aguardar", effect: "Sem mudança.", value: 0 }],
        more: "Quando houver pedidos, as decisões passam a aparecer aqui automaticamente." }));
    }
    return out;
  }

  function decisoesPerguntas(qs) {
    return qs.map((q) => {
      const h = Math.max(0, Math.round((Date.now() - new Date(q.date_created).getTime()) / 3600000));
      const tem = !!q.draft;
      return { id: "q-" + q.id, channel: q.store ? "Mercado Livre · " + q.store : "Mercado Livre", crit: h >= 12 ? "alta" : "normal",
        waiting: "esperando há " + (h < 1 ? "menos de 1 h" : h + " h"),
        title: "Pergunta de comprador: " + (q.item_title || "seu anúncio"),
        detail: "\u201C" + q.text + "\u201D",
        draft: q.draft || "",
        options: [
          { k: "A", label: tem ? "Usar a resposta sugerida" : "Marcar como vista", effect: tem ? q.draft : "Sem sugestão agora. Responda direto no Mercado Livre.", value: 0 },
          { k: "B", label: "Deixar para depois", effect: "A pergunta continua esperando no Mercado Livre.", value: 0 }],
        more: "Resposta feita só com os dados do anúncio. Responder rápido melhora a sua reputação e a chance de venda." };
    });
  }

  /* ---------- avisos urgentes (push) ---------- */
  function b64(s) { const p = "=".repeat((4 - (s.length % 4)) % 4), r = atob((s + p).replace(/-/g, "+").replace(/_/g, "/")); return Uint8Array.from(r, (c) => c.charCodeAt(0)); }
  function chaveB64(buf) { return btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""); }
  async function iniciarAvisos() {
    const box = $("#avisos");
    const pinta = (titulo, texto, botoes) => { box.hidden = false; box.replaceChildren(el("b", { text: titulo }), el("p", { text: texto }), ...(botoes || [])); };
    const ios = /iphone|ipad|ipod/i.test(navigator.userAgent), instalado = navigator.standalone || matchMedia("(display-mode: standalone)").matches;
    if (!("serviceWorker" in navigator && "PushManager" in window && "Notification" in window)) {
      if (ios && !instalado) pinta("Avisos urgentes", "No iPhone, toque em Compartilhar e depois em Adicionar à Tela de Início. Abra o app por lá para ativar os avisos.");
      return;
    }
    const reg = await navigator.serviceWorker.ready.catch(() => null);
    if (!reg) return;
    const sub = await reg.pushManager.getSubscription();
    const teste = el("button", { class: "btn btn-line", type: "button", text: "Enviar aviso de teste", onclick: async (ev) => {
      ev.currentTarget.disabled = true;
      try { await api("/push/teste", { method: "POST" }); toastAviso("Aviso enviado. Ele chega em instantes."); } catch (e) { toastAviso("Não foi possível enviar o teste."); }
      ev.currentTarget.disabled = false;
    } });
    if (sub && Notification.permission === "granted") { pinta("Avisos urgentes ativos", "Você será avisado neste aparelho quando chegar uma pergunta de comprador.", [teste]); return; }
    if (Notification.permission === "denied") { pinta("Avisos bloqueados", "Libere as notificações do P-Vendas nas configurações do aparelho para receber os avisos urgentes."); return; }
    pinta("Receba avisos urgentes", "Quando chegar uma pergunta de comprador, o app avisa na hora. Quem responde rápido vende mais.", [
      el("button", { class: "btn btn-primary", type: "button", text: "Ativar avisos urgentes", onclick: async (ev) => {
        ev.currentTarget.disabled = true;
        try {
          const perm = await Notification.requestPermission();
          if (perm !== "granted") { iniciarAvisos(); return; }
          const k = (await (await fetch(API + "/push/chave")).json()).key;
          const s = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64(k) });
          await api("/push/assinar", { method: "POST", body: { endpoint: s.endpoint, p256dh: chaveB64(s.getKey("p256dh")), auth: chaveB64(s.getKey("auth")) } });
          iniciarAvisos();
        } catch (e) { toastAviso("Não foi possível ativar os avisos neste aparelho."); ev.currentTarget.disabled = false; }
      } })
    ]);
  }

  async function iniciarReal() {
    if (!token()) { mostrarLogin(aviso); return; }
    const pill = document.querySelector(".demo-pill"); pill.textContent = "Carregando…"; pill.classList.add("skel");
    try {
      const [tt, ml, me, contas, perfil, perguntas] = await Promise.all([
        api("/orders/"),
        api("/integrations/mercadolivre/orders").catch((e) => { if (e.sessao) throw e; return []; }),
        api("/integrations/mercadolivre/me").catch((e) => { if (e.sessao) throw e; return {}; }),
        api("/integrations/tiktok/accounts").catch((e) => { if (e.sessao) throw e; return []; }),
        api("/auth/perfil").catch((e) => { if (e.sessao) throw e; return {}; }),
        api("/integrations/mercadolivre/perguntas").catch((e) => { if (e.sessao) throw e; return []; })
      ]);
      tt.forEach((o) => (o.channel = "TikTok Shop"));
      const pedidos = tt.concat(ml).sort((a, b) => String(b.created_at).localeCompare(String(a.created_at)));
      renderLojaReal(pedidos);
      pill.classList.remove("skel"); $("#sair").hidden = false;
      const nome = perfil.name || nomeConta || me.nickname;
      if (nome) $("#saudacao").textContent = "Olá, " + nome;
      const mlOn = !!me.connected, ttOn = contas.length > 0;
      CANAIS[0].on = mlOn; CANAIS[1].on = ttOn;
      CANAIS[0].t = mlOn ? "ok" : "warn"; CANAIS[1].t = ttOn ? "ok" : "warn";
      const lojasML = me.stores || (me.nickname ? [me.nickname] : []);
      CANAIS[0].s = mlOn ? (lojasML.length > 1 ? "Conectado: " + lojasML.length + " lojas" : "Conectado: sua loja") : "Não conectado";
      CANAIS[0].note = mlOn ? ml.length + " pedidos lidos agora de: " + lojasML.join(", ") + ". Para adicionar outra loja, entre antes na conta dela no Mercado Livre." : "Conecte a sua conta para ver os pedidos reais aqui. Você autoriza na página do Mercado Livre.";
      CANAIS[1].s = ttOn ? (contas.length > 1 ? "Conectado: " + contas.length + " lojas" : "Conectado: sua loja") : "Não conectado";
      CANAIS[1].note = ttOn ? tt.length + " pedidos lidos agora da sua conta do TikTok Shop." : "Conecte a sua loja do TikTok Shop. Você autoriza na página do TikTok.";
      CANAIS[0].link = "/integrations/mercadolivre/link"; CANAIS[1].link = "/integrations/tiktok/link";
      renderCanais();
      if (mlOn || ttOn) {
        DECISIONS.splice(0, DECISIONS.length, ...decisoesPerguntas(perguntas || []), ...gerarDecisoes(pedidos, mlOn && ttOn ? "Todos os canais" : mlOn ? "Mercado Livre" : "TikTok Shop"));
        $("#view-hoje .lead-text").textContent = "Os agentes analisaram os seus pedidos reais. Nada é alterado na sua loja sem a sua aprovação.";
        renderHoje();
      }
      pill.textContent = mlOn || ttOn ? "Loja conectada" : "Conta criada"; pill.classList.add("real");
      iniciarAvisos();
      pill.title = "Pedidos reais. As decisões da aba Hoje vêm desses pedidos.";
      if (!mlOn && !ttOn) { $("#view-canais .lead-text").textContent = "Sua conta está pronta. Conecte um marketplace para ver os seus pedidos reais."; irParaCanais(); }
      else if (aviso) { toastAviso(aviso); }
    } catch (e) {
      if (e.sessao) { gravarToken(null); tokenMem = null; mostrarLogin("Sua sessão expirou. Entre de novo."); }
      else { pill.classList.remove("skel"); pill.textContent = "Sem conexão com a loja"; }
    }
  }
  function toastAviso(t) {
    const box = $("#toast"); $("#toast-text").textContent = t; $("#toast-undo").hidden = true; box.hidden = false;
    setTimeout(() => { box.hidden = true; $("#toast-undo").hidden = false; }, 4000);
  }

  iniciarGoogle();
  iniciarReal();

  if ("serviceWorker" in navigator && location.protocol.startsWith("http")) {
    navigator.serviceWorker.register("service-worker.js").catch(() => {});
  }
})();
