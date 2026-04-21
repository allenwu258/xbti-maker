(function () {
  const configEl = document.getElementById("xbti-config");
  const app = document.getElementById("xbti-app");
  if (!configEl || !app) return;

  const config = JSON.parse(configEl.textContent);
  const state = {
    index: 0,
    answers: {},
    visibleQuestions: [],
  };

  const levelValue = { L: 0, M: 1, H: 2 };

  function init() {
    state.visibleQuestions = visibleQuestions();
    renderStart();
  }

  function visibleQuestions() {
    return config.questions.filter((question) => {
      if (!question.display_condition) return true;
      return state.answers[question.display_condition.question_id] === question.display_condition.option_id;
    });
  }

  function renderStart() {
    app.innerHTML = `
      <section class="xbti-screen">
        <p class="xbti-kicker">XBTI TEST</p>
        <h1 class="xbti-title">${escapeHtml(config.meta.name)}</h1>
        <p class="xbti-text">${escapeHtml(config.meta.description || config.meta.subtitle || "")}</p>
        <p class="xbti-text">${escapeHtml(config.meta.disclaimer || "")}</p>
        <button class="xbti-button" id="start">${escapeHtml(config.page.start_button_text || "开始测试")}</button>
      </section>
    `;
    document.getElementById("start").addEventListener("click", () => {
      state.index = 0;
      state.answers = {};
      state.visibleQuestions = visibleQuestions();
      renderQuestion();
    });
  }

  function renderQuestion() {
    state.visibleQuestions = visibleQuestions();
    const question = state.visibleQuestions[state.index];
    if (!question) {
      renderResult();
      return;
    }

    const options = question.options.map((option) => `
      <button class="xbti-option" data-option="${escapeAttr(option.id)}">${escapeHtml(option.text)}</button>
    `).join("");

    app.innerHTML = `
      <section class="xbti-screen">
        <div class="xbti-progress">${state.index + 1} / ${state.visibleQuestions.length}</div>
        <h2 class="xbti-question">${escapeHtml(question.text)}</h2>
        <div class="xbti-options">${options}</div>
        ${state.index > 0 ? '<button class="xbti-button secondary" id="back">上一题</button>' : ""}
      </section>
    `;

    app.querySelectorAll(".xbti-option").forEach((button) => {
      button.addEventListener("click", () => {
        state.answers[question.id] = button.getAttribute("data-option");
        state.index += 1;
        renderQuestion();
      });
    });

    const back = document.getElementById("back");
    if (back) {
      back.addEventListener("click", () => {
        state.index = Math.max(0, state.index - 1);
        renderQuestion();
      });
    }
  }

  function renderResult() {
    const score = calculateScore(config, state.answers);
    const result = config.results.find((item) => item.id === score.result_id) || config.results[0];
    const bars = config.dimensions.map((dimension) => {
      const level = score.dimension_levels[dimension.id] || "M";
      const percent = level === "L" ? 20 : level === "M" ? 55 : 90;
      return `
        <div class="xbti-bar">
          <span>${escapeHtml(dimension.name)}</span>
          <div class="xbti-track"><div class="xbti-fill" style="width: ${percent}%"></div></div>
          <strong>${level}</strong>
        </div>
      `;
    }).join("");

    app.innerHTML = `
      <section class="xbti-screen">
        <span class="xbti-result-code">${escapeHtml(result.code)}</span>
        <h1 class="xbti-title">${escapeHtml(result.name)}</h1>
        <h2 class="xbti-question">${escapeHtml(result.headline)}</h2>
        <p class="xbti-text">${escapeHtml(result.description)}</p>
        <p class="xbti-text">匹配度: ${score.similarity}%</p>
        <div class="xbti-bars">${bars}</div>
        <details class="xbti-debug">
          <summary>评分调试</summary>
          <pre>${escapeHtml(JSON.stringify(score, null, 2))}</pre>
        </details>
        <button class="xbti-button" id="restart">${escapeHtml(config.page.result_button_text || "再测一次")}</button>
      </section>
    `;
    document.getElementById("restart").addEventListener("click", renderStart);
  }

  function calculateScore(config, answers) {
    const dimensionScores = {};
    config.dimensions.forEach((dimension) => {
      dimensionScores[dimension.id] = 0;
    });

    const questionById = Object.fromEntries(config.questions.map((question) => [question.id, question]));
    Object.entries(answers).forEach(([questionId, optionId]) => {
      const question = questionById[questionId];
      if (!question || !question.is_scored || !question.dimension_id) return;
      const option = question.options.find((item) => item.id === optionId);
      if (option && typeof option.score === "number") {
        dimensionScores[question.dimension_id] = (dimensionScores[question.dimension_id] || 0) + option.score;
      }
    });

    const dimensionLevels = {};
    config.dimensions.forEach((dimension) => {
      const questions = config.questions.filter((question) => question.is_scored && question.dimension_id === dimension.id);
      let minScore = 0;
      let maxScore = 0;
      questions.forEach((question) => {
        const scores = question.options.map((option) => option.score).filter((score) => typeof score === "number");
        if (scores.length) {
          minScore += Math.min(...scores);
          maxScore += Math.max(...scores);
        }
      });
      let normalized = maxScore <= minScore ? 0.5 : (dimensionScores[dimension.id] - minScore) / (maxScore - minScore);
      normalized = Math.max(0, Math.min(1, normalized));
      if (normalized <= config.scoring.low_max) {
        dimensionLevels[dimension.id] = "L";
      } else if (normalized <= config.scoring.mid_max) {
        dimensionLevels[dimension.id] = "M";
      } else {
        dimensionLevels[dimension.id] = "H";
      }
    });

    const userVector = config.dimensions.map((dimension) => dimensionLevels[dimension.id]);
    const triggeredRules = (config.rules || [])
      .filter((rule) => answers[rule.question_id] === rule.option_id)
      .sort((a, b) => b.priority - a.priority);

    const standardResults = config.results.filter((result) => result.kind === "standard" && result.template.length === config.dimensions.length);
    const maxDistance = config.dimensions.reduce((total, dimension) => total + (dimension.weight || 1) * 2, 0) || 1;
    const candidates = standardResults.map((result) => {
      let distance = 0;
      let exact = 0;
      result.template.forEach((level, index) => {
        const userLevel = userVector[index];
        if (userLevel === level) exact += 1;
        distance += (config.dimensions[index].weight || 1) * Math.abs(levelValue[userLevel] - levelValue[level]);
      });
      const similarity = Math.max(0, Math.min(100, Math.round((1 - distance / maxDistance) * 100)));
      return {
        result_id: result.id,
        code: result.code,
        name: result.name,
        distance,
        exact_matches: exact,
        similarity,
        priority: result.priority || 0,
      };
    }).sort((a, b) => {
      if (a.distance !== b.distance) return a.distance - b.distance;
      if (a.exact_matches !== b.exact_matches) return b.exact_matches - a.exact_matches;
      if (a.priority !== b.priority) return b.priority - a.priority;
      return a.result_id.localeCompare(b.result_id);
    });

    if (triggeredRules.length) {
      return {
        result_id: triggeredRules[0].result_id,
        similarity: 100,
        dimension_scores: dimensionScores,
        dimension_levels: dimensionLevels,
        user_vector: userVector,
        candidates,
        triggered_rules: [triggeredRules[0].id],
      };
    }

    const winner = candidates[0];
    if (!winner) {
      return {
        result_id: config.scoring.fallback_result_id,
        similarity: 0,
        dimension_scores: dimensionScores,
        dimension_levels: dimensionLevels,
        user_vector: userVector,
        candidates: [],
        triggered_rules: [],
      };
    }
    return {
      result_id: winner.similarity < config.scoring.min_similarity ? config.scoring.fallback_result_id : winner.result_id,
      similarity: winner.similarity,
      dimension_scores: dimensionScores,
      dimension_levels: dimensionLevels,
      user_vector: userVector,
      candidates,
      triggered_rules: [],
    };
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function escapeAttr(value) {
    return escapeHtml(value).replaceAll("`", "&#096;");
  }

  init();
})();
