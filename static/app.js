/**
 * Striper frontend app – routing, auth, analyze form, history, theme.
 * Extracted from inline script for SRP: HTML structure vs JS behavior.
 */
(function () {
  'use strict';

  const AUTH_KEY = 'striper_token';
  const USER_KEY = 'striper_user';
  const THEME_KEY = 'striper_theme';

  const landingPage = document.getElementById('landing-page');
  const loginPage = document.getElementById('login-page');
  const registerPage = document.getElementById('register-page');
  const appPage = document.getElementById('app-page');
  const analyzeSection = document.getElementById('analyze-section');
  const historySection = document.getElementById('history-section');
  const historyListEl = document.getElementById('history-list');
  const userInfoEl = document.getElementById('user-info');
  const historyBtn = document.getElementById('history-btn');
  const logoutBtn = document.getElementById('logout-btn');
  const loginErrorEl = document.getElementById('login-error');
  const registerErrorEl = document.getElementById('register-error');
  const themeToggle = document.getElementById('theme-toggle');
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  const form = document.getElementById('analyze-form');
  const apiKeyInput = document.getElementById('api-key');
  const promptInput = document.getElementById('prompt');
  const inputField = document.getElementById('input');
  const submitBtn = document.getElementById('submit-btn');
  const statusEl = document.getElementById('status');
  const resultsEl = document.getElementById('results');
  const scoreProgress = document.getElementById('score-progress');
  const scoreLabel = document.getElementById('score-label');
  const improvedPromptEl = document.getElementById('improved-prompt');
  const componentsEl = document.getElementById('components');
  const copyImprovedBtn = document.getElementById('copy-improved-btn');
  const useImprovedBtn = document.getElementById('use-improved-btn');
  const clearFormBtn = document.getElementById('clear-form-btn');
  const copyReportBtn = document.getElementById('copy-report-btn');
  const downloadJsonBtn = document.getElementById('download-json-btn');
  const promptCountEl = document.getElementById('prompt-count');
  const inputCountEl = document.getElementById('input-count');
  const promptTemplatesEl = document.getElementById('prompt-templates');

  const PROMPT_TEMPLATES = {
    'customer-support':
      'You are a customer support agent. Be helpful and concise. Always use bullet points. Never use markdown. Respond in under 100 words. End with "Is there anything else I can help with?"',
    'code-review':
      'You are a senior software engineer. Review the code for bugs, security issues, and style. Provide: 1) Summary. 2) Critical issues. 3) Suggestions. Use bullet points. Be concise. Output plain text only.',
    summarization:
      'You are a summarization expert. Summarize the text in 3-5 sentences. Use professional language. Do not include opinions. Output plain text only. Never use markdown.',
    'creative-writing':
      'You are a creative writer. Write engaging, vivid prose. Use varied sentence structure. Include sensory details. Avoid clichés. Keep paragraphs short. Output in plain text.',
  };

  function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }
  function escapeAttr(s) {
    return escapeHtml(s).replace(/"/g, '&quot;');
  }

  function formatCharWordCount(chars, words) {
    return chars + ' chars, ' + words + ' words';
  }

  function clearForm() {
    promptInput.value = '';
    inputField.value = '';
    apiKeyInput.value = '';
    if (promptTemplatesEl) promptTemplatesEl.value = '';
    resultsEl.classList.add('hidden');
    statusEl.textContent = '';
    statusEl.className = 'text-sm text-base-content/70';
    updatePromptCount();
    updateInputCount();
    promptInput.focus();
  }

  let lastAnalysisData = null;

  function updateCharWordCount(textareaEl, targetEl, suffix) {
    const text = textareaEl.value;
    const chars = text.length;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    const count = formatCharWordCount(chars, words);
    targetEl.textContent = suffix ? count + ' · ' + suffix : count;
  }

  function updatePromptCount() {
    updateCharWordCount(promptInput, promptCountEl);
  }

  function updateInputCount() {
    updateCharWordCount(inputField, inputCountEl, 'Sample text the prompt will process');
  }

  promptInput.addEventListener('input', updatePromptCount);
  promptInput.addEventListener('paste', () => setTimeout(updatePromptCount, 0));
  inputField.addEventListener('input', updateInputCount);
  inputField.addEventListener('paste', () => setTimeout(updateInputCount, 0));
  updatePromptCount();
  updateInputCount();

  if (promptTemplatesEl) {
    promptTemplatesEl.addEventListener('change', () => {
      const id = promptTemplatesEl.value;
      if (id && PROMPT_TEMPLATES[id]) {
        promptInput.value = PROMPT_TEMPLATES[id];
        updatePromptCount();
        promptInput.focus();
      }
    });
  }

  function getAuthHeaders() {
    const token = localStorage.getItem(AUTH_KEY);
    const h = { 'Content-Type': 'application/json' };
    if (token) h['Authorization'] = 'Bearer ' + token;
    return h;
  }

  function showFormError(el, msg) {
    el.textContent = msg;
    el.classList.remove('hidden');
  }
  function clearFormError(el) {
    el.textContent = '';
    el.classList.add('hidden');
  }

  function hideAllPages() {
    landingPage.classList.add('hidden');
    loginPage.classList.add('hidden');
    registerPage.classList.add('hidden');
    appPage.classList.add('hidden');
  }

  function showPage(pageId) {
    hideAllPages();
    const page = document.getElementById(pageId);
    if (page) page.classList.remove('hidden');
  }

  function setLoggedIn(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    userInfoEl.textContent = user ? user.username : '';
    historySection.classList.add('hidden');
    showPage('app-page');
    window.location.hash = '#/app';
  }
  function setLoggedOut() {
    localStorage.removeItem(AUTH_KEY);
    localStorage.removeItem(USER_KEY);
    userInfoEl.textContent = '';
    showPage('landing-page');
    window.location.hash = '#/';
  }

  function getRoute() {
    const hash = window.location.hash.slice(1) || '/';
    return hash.startsWith('/') ? hash : '/' + hash;
  }

  /**
   * Resolve path + auth to page and optional redirect. SRP: single place for routing rules.
   * Returns { pageId, redirect? }.
   */
  function resolveRoute(path, isAuth) {
    if (isAuth) {
      if (path === '/' || path === '/login' || path === '/register') return { pageId: 'app-page', redirect: '#/app' };
      if (path === '/app') return { pageId: 'app-page' };
    } else {
      if (path === '/app') return { pageId: 'login-page', redirect: '#/login' };
      if (path === '/') return { pageId: 'landing-page' };
      if (path === '/login') return { pageId: 'login-page' };
      if (path === '/register') return { pageId: 'register-page' };
    }
    return { pageId: 'landing-page', redirect: '#/' };
  }

  function route() {
    const path = getRoute();
    const isAuth = !!localStorage.getItem(AUTH_KEY);
    const { pageId, redirect } = resolveRoute(path, isAuth);
    if (redirect) window.location.hash = redirect;
    showPage(pageId);
  }

  const THEMES = ['dark', 'light', 'system'];

  function getEffectiveTheme(preference) {
    if (preference === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return preference;
  }

  function applyTheme(preference) {
    const effective = getEffectiveTheme(preference);
    document.documentElement.setAttribute('data-theme', effective);
    const icons = { dark: '🌙', light: '☀️', system: '🌐' };
    const labels = { dark: 'Switch to light', light: 'Switch to dark', system: 'Switch to dark' };
    themeToggle.textContent = icons[preference] || icons.dark;
    themeToggle.setAttribute('aria-label', (labels[preference] || labels.dark) + ' theme');
    localStorage.setItem(THEME_KEY, preference);
  }

  const savedTheme = localStorage.getItem(THEME_KEY) || 'dark';
  applyTheme(savedTheme);

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (localStorage.getItem(THEME_KEY) === 'system') {
      document.documentElement.setAttribute('data-theme', getEffectiveTheme('system'));
    }
  });

  themeToggle.addEventListener('click', () => {
    const current = localStorage.getItem(THEME_KEY) || 'dark';
    const idx = THEMES.indexOf(current);
    const next = THEMES[(idx + 1) % THEMES.length];
    applyTheme(next);
  });

  window.addEventListener('hashchange', route);
  route();

  async function submitAuthForm(endpoint, payload, errorEl, defaultError, btnEl, loadingText) {
    clearFormError(errorEl);
    let originalText = '';
    if (btnEl && loadingText) {
      btnEl.disabled = true;
      originalText = btnEl.textContent;
      btnEl.textContent = loadingText;
    }
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || defaultError);
      localStorage.setItem(AUTH_KEY, data.access_token);
      setLoggedIn(data.user);
    } catch (err) {
      showFormError(errorEl, err.message);
    } finally {
      if (btnEl) {
        btnEl.disabled = false;
        btnEl.textContent = originalText;
      }
    }
  }

  const loginSubmitBtn = document.getElementById('login-submit-btn');
  const registerSubmitBtn = document.getElementById('register-submit-btn');

  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(loginForm);
    await submitAuthForm(
      '/login',
      { username: fd.get('username'), password: fd.get('password') },
      loginErrorEl,
      'Login failed',
      loginSubmitBtn,
      'Logging in...'
    );
  });

  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(registerForm);
    await submitAuthForm(
      '/register',
      {
        username: fd.get('username'),
        email: fd.get('email'),
        password: fd.get('password'),
      },
      registerErrorEl,
      'Registration failed',
      registerSubmitBtn,
      'Creating account...'
    );
  });

  logoutBtn.addEventListener('click', () => { setLoggedOut(); });

  async function loadHistory() {
    analyzeSection.classList.add('hidden');
    historySection.classList.remove('hidden');
    historyListEl.innerHTML = '<li class="text-base-content/70">Loading...</li>';
    try {
      const res = await fetch('/history', { headers: getAuthHeaders() });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to load history');
      historyListEl.innerHTML = data.items.length === 0
        ? '<li class="text-base-content/70">No history yet.</li>'
        : data.items.map(item =>
            `<li class="card bg-base-200 border border-base-300 p-4 cursor-pointer hover:bg-base-300 transition-colors history-item" data-prompt="${escapeAttr(item.prompt)}" title="Click to re-analyze">
              <p class="font-mono text-sm mb-2">${escapeHtml(item.prompt.slice(0, 100))}${item.prompt.length > 100 ? '…' : ''}</p>
              <p class="text-xs text-base-content/60">Score: ${Math.round(item.over_engineered_score * 100)}% · ${item.created_at} · <span class="text-primary">Click to re-analyze</span></p>
            </li>`
          ).join('');
      document.querySelectorAll('.history-item').forEach(el => {
        el.addEventListener('click', () => {
          const prompt = el.getAttribute('data-prompt');
          if (prompt) {
            promptInput.value = prompt;
            historySection.classList.add('hidden');
            analyzeSection.classList.remove('hidden');
            promptInput.focus();
          }
        });
      });
    } catch (err) {
      historyListEl.innerHTML = '<li class="text-error">' + escapeHtml(err.message) + '</li>';
    }
  }

  historyBtn.addEventListener('click', loadHistory);

  document.getElementById('history-back').addEventListener('click', () => {
    historySection.classList.add('hidden');
    analyzeSection.classList.remove('hidden');
  });

  const exportHistoryBtn = document.getElementById('export-history-btn');
  const exportHistoryError = document.getElementById('export-history-error');
  if (exportHistoryBtn && exportHistoryError) {
    exportHistoryBtn.addEventListener('click', async () => {
      exportHistoryError.textContent = '';
      exportHistoryError.classList.add('hidden');
      try {
        const res = await fetch('/history', { headers: getAuthHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to load history');
        const blob = new Blob([JSON.stringify(data, null, 2)], {
          type: 'application/json',
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'striper-history.json';
        a.click();
        URL.revokeObjectURL(url);
      } catch (err) {
        exportHistoryError.textContent = err.message || 'Export failed';
        exportHistoryError.classList.remove('hidden');
      }
    });
  }

  clearFormBtn.addEventListener('click', clearForm);

  useImprovedBtn.addEventListener('click', () => {
    const text = improvedPromptEl.textContent || '';
    if (!text || text === '(unchanged)') return;
    promptInput.value = text;
    updatePromptCount();
    promptInput.focus();
  });

  async function copyWithFeedback(text, btnEl) {
    if (!text) return;
    const originalLabel = btnEl.textContent;
    try {
      await navigator.clipboard.writeText(text);
      btnEl.textContent = 'Copied!';
    } catch {
      btnEl.textContent = 'Copy failed';
    }
    setTimeout(() => { btnEl.textContent = originalLabel; }, 1500);
  }

  copyImprovedBtn.addEventListener('click', () =>
    copyWithFeedback(improvedPromptEl.textContent || '', copyImprovedBtn)
  );

  function buildReportText(data) {
    if (!data) return '';
    const score = Math.round((data.over_engineered_score || 0) * 100);
    const improved = data.improved_prompt || '(unchanged)';
    const kept = (data.components_kept || []).map((c) => '  - ' + c).join('\n');
    const removed = (data.components_removed || []).map((c) => '  - ' + c).join('\n');
    return [
      'Over-engineered score: ' + score + '%',
      '',
      'Improved prompt:',
      improved,
      '',
      'Components kept:',
      kept || '  (none)',
      '',
      'Components removed:',
      removed || '  (none)',
    ].join('\n');
  }

  copyReportBtn.addEventListener('click', () =>
    copyWithFeedback(buildReportText(lastAnalysisData), copyReportBtn)
  );

  downloadJsonBtn.addEventListener('click', () => {
    if (!lastAnalysisData) return;
    const blob = new Blob([JSON.stringify(lastAnalysisData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'striper-analysis.json';
    a.click();
    URL.revokeObjectURL(url);
  });

  function handleCtrlEnter(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (!analyzeSection.classList.contains('hidden') && historySection.classList.contains('hidden')) {
        form.requestSubmit();
      }
    }
  }
  promptInput.addEventListener('keydown', handleCtrlEnter);
  inputField.addEventListener('keydown', handleCtrlEnter);

  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'H') {
      e.preventDefault();
      if (localStorage.getItem(AUTH_KEY) && !appPage.classList.contains('hidden')) {
        historyBtn.click();
      }
    }
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'R') {
      e.preventDefault();
      if (!historySection.classList.contains('hidden')) {
        loadHistory();
      }
    }
    if (e.key === 'Escape' && !historySection.classList.contains('hidden')) {
      historySection.classList.add('hidden');
      analyzeSection.classList.remove('hidden');
    }
  });

  function buildAnalyzeRequestBody(prompt, inputText, apiKey) {
    const body = { prompt };
    if (inputText) body.input = inputText;
    if (apiKey) body.api_key = apiKey;
    return body;
  }

  function renderScoreSection(data) {
    const score = data.over_engineered_score;
    const pct = Math.round(score * 100);
    scoreProgress.value = pct;
    scoreProgress.className = 'progress w-full h-2 ' + (
      score < 0.33 ? 'progress-success' :
      score < 0.66 ? 'progress-warning' :
      'progress-error'
    );
    scoreLabel.textContent = pct + '% – ' + (
      score < 0.33 ? 'prompt is fairly optimal' :
      score < 0.66 ? 'some redundancy detected' :
      'prompt is over-engineered'
    );
  }

  function renderComponentsSection(data) {
    const items = [];
    (data.components_kept || []).forEach(c => { items.push({ text: c, type: 'kept' }); });
    (data.components_removed || []).forEach(c => { items.push({ text: c, type: 'removed' }); });
    componentsEl.innerHTML = items.map(({ text, type }) =>
      `<li class="flex items-start gap-2 py-3 text-sm">
        <span class="badge badge-sm shrink-0 ${type === 'kept' ? 'badge-success' : 'badge-error'}">${type}</span>
        <span>${escapeHtml(text)}</span>
      </li>`
    ).join('');
  }

  async function handleAnalyzeSubmit(e) {
    e.preventDefault();
    const prompt = promptInput.value.trim();
    if (!prompt) return;

    submitBtn.disabled = true;
    statusEl.textContent = 'Analyzing...';
    statusEl.className = 'text-sm text-primary';
    resultsEl.classList.add('hidden');
    const startTime = Date.now();

    try {
      const body = buildAnalyzeRequestBody(
        prompt,
        inputField.value.trim() || null,
        apiKeyInput.value.trim()
      );
      const res = await fetch('/analyze', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(body),
      });
      const data = await res.json();

      if (!res.ok) {
        if (res.status === 401) {
          setLoggedOut();
          throw new Error('Session expired. Please log in again.');
        }
        throw new Error(data.detail || 'Analysis failed');
      }

      renderScoreSection(data);
      improvedPromptEl.textContent = data.improved_prompt || '(unchanged)';
      lastAnalysisData = data;
      renderComponentsSection(data);

      resultsEl.classList.remove('hidden');
      const durationSec = ((Date.now() - startTime) / 1000).toFixed(1);
      statusEl.textContent = `Done · Analyzed in ${durationSec}s`;
      statusEl.className = 'text-sm text-base-content/70';
    } catch (err) {
      statusEl.textContent = err.message || 'Error';
      statusEl.className = 'text-sm text-error';
    } finally {
      submitBtn.disabled = false;
    }
  }

  form.addEventListener('submit', handleAnalyzeSubmit);
})();
