(function () {
  const copyButtons = document.querySelectorAll("[data-copy-target]");
  copyButtons.forEach((button) => {
    button.addEventListener("click", async () => {
      const target = document.getElementById(button.dataset.copyTarget);
      if (!target) return;
      try {
        await navigator.clipboard.writeText(target.textContent.trim());
        button.textContent = "已复制";
        setTimeout(() => (button.textContent = "复制 curl"), 1200);
      } catch (_err) {
        button.textContent = "复制失败";
      }
    });
  });

  const form = document.getElementById("api-form");
  if (!form || !window.FieldLabApi) return;

  const responseBox = document.getElementById("api-response");
  const curlBox = document.getElementById("api-curl");

  const renderCurl = (customer, minTotal) => {
    curlBox.textContent = `curl -s ${window.location.origin}${window.FieldLabApi.endpoint} -H 'Content-Type: application/json' -d '{"customer":"${customer}","min_total":"${minTotal}"}'`;
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const payload = {
      customer: formData.get("customer"),
      min_total: formData.get("min_total"),
    };
    renderCurl(payload.customer, payload.min_total);
    responseBox.textContent = "请求发送中...";
    try {
      const response = await fetch(window.FieldLabApi.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      responseBox.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
      responseBox.textContent = `请求失败: ${error}`;
    }
  });
})();
