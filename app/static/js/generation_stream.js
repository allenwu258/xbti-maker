(function () {
  const form = document.getElementById("generation-form");
  if (!form || !window.fetch || !window.TextDecoder) return;

  const reasoningEl = document.getElementById("reasoning-output");
  const outputEl = document.getElementById("model-output");
  const statusEl = document.getElementById("generation-status");
  const resultEl = document.getElementById("generation-result");
  const button = document.getElementById("generate-button");
  const streamEndpoint = form.dataset.streamEndpoint;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    setStatus("连接中");
    clearPanels();
    button.disabled = true;

    try {
      const payload = serializeForm(form);
      const response = await fetch(streamEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "text/event-stream",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok || !response.body) {
        const text = await response.text();
        throw new Error(text || `请求失败: HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\n\n");
        buffer = chunks.pop() || "";
        for (const chunk of chunks) {
          handleSseChunk(chunk);
        }
      }

      if (buffer.trim()) {
        handleSseChunk(buffer);
      }
    } catch (error) {
      setStatus("失败");
      appendResult(`<div class="alert error">${escapeHtml(error.message || String(error))}</div>`);
    } finally {
      button.disabled = false;
    }
  });

  function serializeForm(formEl) {
    const data = new FormData(formEl);
    return {
      name: data.get("name") || "",
      topic: data.get("topic") || "",
      audience: data.get("audience") || "",
      tone: data.get("tone") || "",
      platform: data.get("platform") || "",
      provider: data.get("provider") || "ark",
      question_count: Number(data.get("question_count") || 30),
      dimension_count: Number(data.get("dimension_count") || 15),
      result_count: Number(data.get("result_count") || 24),
      allow_hidden_results: data.get("allow_hidden_results") === "on",
      safety_level: "normal",
    };
  }

  function handleSseChunk(chunk) {
    let event = "message";
    let data = "";
    chunk.split("\n").forEach((line) => {
      if (line.startsWith("event:")) {
        event = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        data += line.slice(5).trim();
      }
    });

    if (!data || data === "[DONE]") {
      return;
    }

    const payload = JSON.parse(data);
    if (event === "status") {
      setStatus(payload.message || "进行中");
    } else if (event === "reasoning") {
      appendText(reasoningEl, payload.delta || "");
      setStatus("思考中");
    } else if (event === "output") {
      appendText(outputEl, payload.delta || "");
      setStatus("输出中");
    } else if (event === "project_created") {
      setStatus("已完成");
      resultEl.innerHTML = `
        <div class="alert success">项目已创建，生成 provider: ${escapeHtml(payload.provider || "unknown")}</div>
        <div class="actions">
          <a class="button" href="${escapeHtml(payload.editor_url)}">进入编辑器</a>
          <a class="button secondary" href="${escapeHtml(payload.preview_url)}">打开预览</a>
        </div>
      `;
    } else if (event === "error") {
      setStatus("失败");
      appendResult(`<div class="alert error">${escapeHtml(payload.message || "生成失败")}</div>`);
    } else if (event === "done") {
      setStatus("已完成");
    }
  }

  function clearPanels() {
    reasoningEl.textContent = "";
    outputEl.textContent = "";
    reasoningEl.classList.remove("muted");
    outputEl.classList.remove("muted");
    resultEl.innerHTML = "生成中...";
  }

  function appendText(target, text) {
    target.textContent += text;
    target.scrollTop = target.scrollHeight;
  }

  function appendResult(html) {
    resultEl.innerHTML = html;
  }

  function setStatus(text) {
    if (statusEl) {
      statusEl.textContent = text;
    }
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }
})();
