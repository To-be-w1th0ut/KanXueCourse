(function () {
  const eventList = document.getElementById("event-list");

  async function loadEvents() {
    if (!eventList) return;
    try {
      const response = await fetch("/api/lab-events");
      const data = await response.json();
      const rows = data.rows || [];
      if (!rows.length) {
        eventList.innerHTML = '<li class="muted">等待浏览器侧事件...</li>';
        return;
      }
      eventList.innerHTML = rows
        .map(
          (row) =>
            `<li><strong>${escapeHtml(row.lab_slug)}</strong><span>${escapeHtml(row.message)}</span><em>${escapeHtml(
              row.created_at
            )}</em></li>`
        )
        .join("");
    } catch (error) {
      eventList.innerHTML = `<li class="muted">event load failed: ${escapeHtml(String(error))}</li>`;
    }
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  async function pushEvent(payload) {
    await fetch("/api/lab-events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await loadEvents();
  }

  async function clearEvents() {
    await fetch("/api/lab-events", { method: "DELETE" });
    await loadEvents();
  }

  const queued = Array.isArray(window.fieldlab && window.fieldlab._queue) ? [...window.fieldlab._queue] : [];
  window.fieldlab = {
    record: async function (lab, message, source = "browser") {
      await pushEvent({ lab, message, source });
    },
  };
  Promise.resolve().then(async () => {
    await loadEvents();
    for (const item of queued) {
      await pushEvent(item);
    }
  });

  document.querySelector("[data-clear-events]")?.addEventListener("click", clearEvents);

  const hashLab = document.getElementById("hash-render-lab");
  if (hashLab) {
    const preview = document.getElementById("hash-preview");
    const input = document.getElementById("hash-input");
    const mode = hashLab.dataset.mode;
    const renderHash = () => {
      const value = decodeURIComponent((window.location.hash || "").replace(/^#/, ""));
      if (!value) {
        preview.textContent = "hash 内容会渲染在这里";
        return;
      }
      if (mode === "vuln") {
        preview.innerHTML = value;
      } else {
        preview.textContent = value;
      }
    };
    document.getElementById("set-hash-btn")?.addEventListener("click", () => {
      window.location.hash = encodeURIComponent(input.value || "");
      renderHash();
    });
    document.getElementById("render-hash-btn")?.addEventListener("click", renderHash);
    window.addEventListener("hashchange", renderHash);
    renderHash();
  }

  const apiLab = document.getElementById("api-template-lab");
  if (apiLab && window.FieldLabApiSearch) {
    const form = document.getElementById("api-template-form");
    const results = document.getElementById("api-search-results");
    const header = document.getElementById("api-search-header");
    form?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const q = new FormData(form).get("q") || "";
      const response = await fetch(`${window.FieldLabApiSearch.endpoint}?q=${encodeURIComponent(String(q))}`);
      const data = await response.json();
      if (window.FieldLabApiSearch.mode === "vuln") {
        header.innerHTML = `Search results for: <mark>${data.query}</mark>`;
        results.innerHTML = (data.rows || [])
          .map(
            (row) =>
              `<article class="feed-card"><div class="feed-meta"><strong>${row.title}</strong><span class="muted mono">${row.tag}</span></div><div class="feed-body">${row.snippet}</div></article>`
          )
          .join("");
      } else {
        header.textContent = `Search results for: ${data.query}`;
        results.innerHTML = "";
        (data.rows || []).forEach((row) => {
          const card = document.createElement("article");
          card.className = "feed-card";
          const meta = document.createElement("div");
          meta.className = "feed-meta";
          const strong = document.createElement("strong");
          strong.textContent = row.title;
          const span = document.createElement("span");
          span.className = "muted mono";
          span.textContent = row.tag;
          meta.append(strong, span);
          const body = document.createElement("div");
          body.className = "feed-body";
          body.textContent = row.snippet;
          card.append(meta, body);
          results.append(card);
        });
      }
    });
  }

  if (window.FieldLabPostMessage) {
    document.getElementById("postmessage-send")?.addEventListener("click", () => {
      const frame = document.getElementById("postmessage-frame");
      const content = document.getElementById("postmessage-input").value || "";
      frame.contentWindow.postMessage({ card: content }, window.FieldLabPostMessage.receiverOrigin);
    });
  }
})();
