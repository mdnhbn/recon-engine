const homeView = document.getElementById("home-view");
const resultsView = document.getElementById("results-view");
const loading = document.getElementById("loading");
const errorBox = document.getElementById("error-box");
const resultsContent = document.getElementById("results-content");

document.getElementById("search-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const value = document.getElementById("search-input").value.trim();
  if (value) runRecon(value);
});

document.getElementById("search-form-top").addEventListener("submit", (e) => {
  e.preventDefault();
  const value = document.getElementById("search-input-top").value.trim();
  if (value) runRecon(value);
});

async function runRecon(target) {
  homeView.classList.add("hidden");
  resultsView.classList.remove("hidden");
  document.getElementById("search-input-top").value = target;

  errorBox.classList.add("hidden");
  resultsContent.innerHTML = "";
  loading.classList.remove("hidden");

  try {
    const resp = await fetch("/api/recon", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target }),
    });
    const data = await resp.json();
    loading.classList.add("hidden");

    if (!resp.ok) {
      errorBox.textContent = data.error || "কিছু একটা সমস্যা হয়েছে।";
      errorBox.classList.remove("hidden");
      return;
    }
    renderResults(data);
    const quotaEl = document.querySelector(".quota");
    if (quotaEl && data.scans_today !== undefined) {
      quotaEl.innerHTML = `আজকে স্ক্যান করেছো: <strong>${data.scans_today}</strong> / ${data.daily_limit}`;
    }
  } catch (err) {
    loading.classList.add("hidden");
    errorBox.textContent = "সার্ভারের সাথে যোগাযোগ করা যায়নি: " + err.message;
    errorBox.classList.remove("hidden");
  }
}

function renderResults(data) {
  let html = "";

  // Whois
  html += `<div class="section"><h3>Whois</h3><div class="card">${renderKV(data.whois)}</div></div>`;

  // DNS
  html += `<div class="section"><h3>DNS Records</h3><div class="card">${renderDNS(data.dns)}</div></div>`;

  // Subdomains
  const allSubs = [...new Set([...(data.passive_subdomains || []), ...(data.active_subdomains || [])])];
  html += `<div class="section"><h3>সাবডোমেইন (${allSubs.length} টি পাওয়া গেছে)</h3>
    <div class="card">
      <div class="sub-list">${allSubs.map(s => `<div>${escapeHtml(s)}</div>`).join("") || "<div>কিছু পাওয়া যায়নি</div>"}</div>
    </div></div>`;

  // Live hosts + tech stack
  html += `<div class="section"><h3>লাইভ হোস্ট ও টেক স্ট্যাক (${(data.live_hosts || []).length} টি)</h3>`;
  (data.live_hosts || []).forEach(host => {
    const statusClass = host.status_code < 300 ? "ok" : host.status_code < 400 ? "warn" : "bad";
    html += `
      <div class="card host-card">
        <div class="host-top">
          <a class="host-url" href="${host.url}" target="_blank" rel="noopener">${escapeHtml(host.host)}</a>
          <span class="status ${statusClass}">${host.status_code}</span>
        </div>
        ${host.title ? `<div class="host-title">${escapeHtml(host.title)}</div>` : ""}
        <div class="chip-list" style="margin-top:10px;">
          ${(host.tech_stack || []).map(t => `<span class="chip">${escapeHtml(t)}</span>`).join("") || "<span class='chip'>শনাক্ত হয়নি</span>"}
        </div>
        ${host.shodan ? `<div class="host-title" style="margin-top:8px;">Shodan: ${escapeHtml(JSON.stringify(host.shodan))}</div>` : ""}
        ${host.censys ? `<div class="host-title">Censys: ${escapeHtml(JSON.stringify(host.censys))}</div>` : ""}
      </div>`;
  });
  if (!(data.live_hosts || []).length) {
    html += `<div class="card">কোনো host লাইভ পাওয়া যায়নি।</div>`;
  }
  html += `</div>`;

  resultsContent.innerHTML = html;
}

function renderKV(obj) {
  if (!obj) return "তথ্য পাওয়া যায়নি";
  if (obj.error) return `<div style="color:var(--bad)">${escapeHtml(obj.error)}</div>`;
  let rows = "";
  for (const [k, v] of Object.entries(obj)) {
    if (v === null || v === undefined || v === "") continue;
    rows += `<div class="k">${escapeHtml(k)}</div><div class="v">${escapeHtml(String(v))}</div>`;
  }
  return `<div class="kv">${rows || "তথ্য পাওয়া যায়নি"}</div>`;
}

function renderDNS(dns) {
  if (!dns) return "তথ্য পাওয়া যায়নি";
  if (dns.error) return `<div style="color:var(--bad)">${escapeHtml(dns.error)}</div>`;
  let rows = "";
  for (const [k, v] of Object.entries(dns)) {
    if (!v || (Array.isArray(v) && v.length === 0)) continue;
    const val = Array.isArray(v) ? v.join(", ") : v;
    rows += `<div class="k">${escapeHtml(k)}</div><div class="v">${escapeHtml(String(val))}</div>`;
  }
  return `<div class="kv">${rows || "তথ্য পাওয়া যায়নি"}</div>`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

