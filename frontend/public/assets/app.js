// Клиентская часть: создание короткой ссылки и список «Мои ссылки».
// Список кодов хранится в localStorage браузера, статистика запрашивается у API.

const STORAGE_KEY = "myLinks";
const MAX_LINKS = 20;

const $ = (id) => document.getElementById(id);

function loadCodes() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch {
    return [];
  }
}

function saveCode(code) {
  const codes = [code, ...loadCodes().filter((c) => c !== code)].slice(0, MAX_LINKS);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(codes));
  } catch {
    /* хранилище недоступно (приватный режим) — просто не запоминаем */
  }
}

async function api(path, options = {}) {
  const resp = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const detail = typeof data.detail === "string" ? data.detail : null;
    throw new Error(detail || (resp.status === 429 ? "Слишком много запросов, подождите минуту" : `Ошибка ${resp.status}`));
  }
  return data;
}

function showError(text) {
  $("error").textContent = text;
  $("error").hidden = !text;
}

function showResult(link) {
  $("short").href = link.short_url;
  $("short").textContent = link.short_url;
  $("result").hidden = false;
}

async function renderLinks() {
  const codes = loadCodes();
  const tbody = $("links").querySelector("tbody");
  $("empty").hidden = codes.length > 0;
  $("links").hidden = codes.length === 0;
  if (!codes.length) return;

  const rows = await Promise.all(codes.map((code) => api(`/api/links/${code}`).catch(() => null)));
  tbody.replaceChildren(
    ...rows.filter(Boolean).map((link) => {
      const tr = document.createElement("tr");
      const a = document.createElement("a");
      a.href = link.short_url;
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = link.short_url.replace(/^https?:\/\//, "");
      const target = document.createElement("td");
      target.className = "target";
      target.textContent = link.target_url;
      target.title = link.target_url;
      const clicks = document.createElement("td");
      clicks.className = "num";
      clicks.textContent = link.clicks;
      const first = document.createElement("td");
      first.append(a);
      tr.append(first, target, clicks);
      return tr;
    })
  );
}

$("form").addEventListener("submit", async (event) => {
  event.preventDefault();
  showError("");
  const url = $("url").value.trim();
  const alias = $("alias").value.trim();
  $("submit").disabled = true;
  try {
    const link = await api("/api/links", {
      method: "POST",
      body: JSON.stringify({ url, alias: alias || null }),
    });
    showResult(link);
    saveCode(link.code);
    $("form").reset();
    renderLinks();
  } catch (err) {
    $("result").hidden = true;
    showError(err.message);
  } finally {
    $("submit").disabled = false;
  }
});

$("copy").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText($("short").href);
    $("copy").textContent = "Скопировано";
    setTimeout(() => ($("copy").textContent = "Копировать"), 1500);
  } catch {
    showError("Не удалось скопировать — выделите ссылку вручную");
  }
});

$("refresh").addEventListener("click", renderLinks);

renderLinks();
