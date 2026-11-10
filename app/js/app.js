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
    const finish = () => {
      decided[id] = { opt: opt, via: via, at: Date.now() };
      save(decided);
      renderHoje();
      const d = DECISIONS.find((x) => x.id === id);
      showToast("Opção " + opt + " aprovada: " + d.title, id);
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
    { n: "Shopee, via Bling", s: "Aguardando liberação do Bling", t: "warn", note: "O app no Bling ainda está em desenvolvimento e só aceita o dono da conta. Falta homologar." },
    { n: "WhatsApp", s: "Em configuração", t: "warn", note: "O servidor está instalado. Faltam as 3 conversas por loja: pré-venda, venda e pós-venda." },
    { n: "Claude, a IA dos agentes", s: "Ativo", t: "ok", note: "Modelo rápido para a rotina e modelo avançado para decisões difíceis. O consumo é registrado por loja." },
    { n: "Shein", s: "Planejado", t: "off", note: "Entra depois que Mercado Livre, TikTok e Shopee estiverem estáveis." }
  ];
  function renderCanais() {
    const ul = $("#canais");
    ul.replaceChildren();
    CANAIS.forEach((c) => ul.append(el("li", {}, [
      el("span", { class: "dot " + c.t, "aria-hidden": "true" }),
      el("div", {}, [el("div", { class: "ch-name", text: c.n }), el("div", { class: "ch-status " + c.t, text: c.s })]),
      el("p", { class: "ch-note", text: c.note })
    ])));
  }

  /* ---------- aba Loja (números fictícios, sempre iguais) ---------- */
  function rng(seed) { let s = seed; return () => ((s = (s * 16807) % 2147483647) / 2147483647); }
  const CH = [
    { id: "total", n: "Total" }, { id: "ml", n: "Mercado Livre", seed: 11, base: 1500 },
    { id: "tt", n: "TikTok Shop", seed: 23, base: 900 }, { id: "sp", n: "Shopee", seed: 37, base: 700 }
  ];
  const DIAS = ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"];
  function serie(c) {
    const r = rng(c.seed), out = [];
    for (let i = 0; i < 7; i++) out.push(Math.round(c.base * (0.65 + r() * 0.7)));
    return out;
  }
  const SERIES = {};
  CH.slice(1).forEach((c) => (SERIES[c.id] = serie(c)));
  SERIES.total = SERIES.ml.map((v, i) => v + SERIES.tt[i] + SERIES.sp[i]);
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

  if ("serviceWorker" in navigator && location.protocol.startsWith("http")) {
    navigator.serviceWorker.register("service-worker.js").catch(() => {});
  }
})();
