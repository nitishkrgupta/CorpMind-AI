(function () {
  // Read target API URL from the script tag's data-api-url attribute or default to current origin
  const currentScript = document.currentScript || (function() {
    const scripts = document.getElementsByTagName('script');
    return scripts[scripts.length - 1];
  })();
  const apiUrl = (currentScript && currentScript.getAttribute('data-api-url')) || window.location.origin;

  // Prevent multiple injections
  if (document.getElementById('docanalyzer-widget-container')) return;

  // Dynamically load marked.js for structured markdown rendering if not already present
  if (!window.marked) {
    const markedScript = document.createElement('script');
    markedScript.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
    document.head.appendChild(markedScript);
  }

  // Inject Styles
  const style = document.createElement('style');
  style.innerHTML = `
    #docanalyzer-widget-container {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 999999;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    #docanalyzer-launcher {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, #2563eb, #1d4ed8);
      color: white;
      border: none;
      box-shadow: 0 8px 24px rgba(37, 99, 235, 0.35);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.25s ease-in-out;
    }

    #docanalyzer-launcher:hover {
      transform: scale(1.06);
      box-shadow: 0 10px 28px rgba(37, 99, 235, 0.45);
    }

    #docanalyzer-launcher svg {
      width: 28px;
      height: 28px;
      transition: transform 0.2s;
    }

    #docanalyzer-chat-window {
      display: none;
      position: absolute;
      bottom: 75px;
      right: 0;
      width: 400px;
      height: 580px;
      min-width: 320px;
      min-height: 380px;
      max-width: calc(100vw - 32px);
      max-height: calc(100vh - 90px);
      background: #ffffff;
      border-radius: 18px;
      box-shadow: 0 12px 36px rgba(0, 0, 0, 0.15);
      border: 1px solid #e2e8f0;
      flex-direction: column;
      overflow: hidden;
      animation: docanalyzer-slide-up 0.25s ease-out;
      transition: width 0.2s cubic-bezier(0.16, 1, 0.3, 1), height 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }

    #docanalyzer-chat-window.docanalyzer-no-transition {
      transition: none !important;
    }

    #docanalyzer-chat-window.docanalyzer-expanded {
      width: min(880px, calc(100vw - 32px)) !important;
      height: min(800px, calc(100vh - 95px)) !important;
    }

    /* Resize Handles */
    .docanalyzer-resizer {
      position: absolute;
      z-index: 100;
    }

    /* Top-Left Diagonal Corner Handle (Width + Height) */
    .docanalyzer-resizer-tl {
      top: 0;
      left: 0;
      width: 22px;
      height: 22px;
      cursor: nwse-resize;
      display: flex;
      align-items: center;
      justify-content: center;
      color: rgba(255, 255, 255, 0.6);
      border-top-left-radius: 18px;
      transition: color 0.15s, background 0.15s;
    }

    .docanalyzer-resizer-tl:hover {
      color: #ffffff;
      background: rgba(255, 255, 255, 0.2);
    }

    /* Top Edge Handle (Height) */
    .docanalyzer-resizer-t {
      top: 0;
      left: 22px;
      right: 0;
      height: 7px;
      cursor: ns-resize;
    }
    .docanalyzer-resizer-t:hover {
      background: rgba(37, 99, 235, 0.25);
    }

    /* Left Edge Handle (Width) */
    .docanalyzer-resizer-l {
      top: 22px;
      left: 0;
      bottom: 0;
      width: 7px;
      cursor: ew-resize;
    }
    .docanalyzer-resizer-l:hover {
      background: rgba(37, 99, 235, 0.25);
    }

    @keyframes docanalyzer-slide-up {
      from { opacity: 0; transform: translateY(16px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .docanalyzer-header {
      background: #2563eb;
      color: white;
      padding: 13px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: relative;
    }

    .docanalyzer-header-title {
      font-weight: 700;
      font-size: 0.98rem;
      letter-spacing: -0.2px;
    }

    .docanalyzer-header-sub {
      font-size: 0.74rem;
      opacity: 0.9;
    }

    .docanalyzer-header-controls {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .docanalyzer-icon-btn {
      background: rgba(255, 255, 255, 0.15);
      border: none;
      color: white;
      cursor: pointer;
      width: 28px;
      height: 28px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0;
      font-size: 1.25rem;
      line-height: 1;
      transition: all 0.2s;
    }

    .docanalyzer-icon-btn:hover {
      background: rgba(255, 255, 255, 0.3);
      transform: scale(1.05);
    }

    .docanalyzer-messages {
      flex: 1;
      padding: 16px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 12px;
      background: #f8fafc;
    }

    .docanalyzer-msg {
      max-width: 90%;
      padding: 12px 16px;
      border-radius: 14px;
      font-size: 0.88rem;
      line-height: 1.55;
      word-break: break-word;
    }

    .docanalyzer-msg-user {
      align-self: flex-end;
      background: #2563eb;
      color: white;
      border-bottom-right-radius: 2px;
    }

    .docanalyzer-msg-bot {
      align-self: flex-start;
      background: #ffffff;
      color: #1e293b;
      border: 1px solid #e2e8f0;
      border-bottom-left-radius: 2px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }

    /* Structured Markdown Styling */
    .docanalyzer-msg-bot p {
      margin: 0 0 8px 0;
    }
    .docanalyzer-msg-bot p:last-child {
      margin-bottom: 0;
    }
    .docanalyzer-msg-bot h1,
    .docanalyzer-msg-bot h2,
    .docanalyzer-msg-bot h3,
    .docanalyzer-msg-bot h4 {
      margin: 10px 0 6px 0;
      font-size: 0.96rem;
      font-weight: 700;
      color: #0f172a;
    }
    .docanalyzer-msg-bot h1:first-child,
    .docanalyzer-msg-bot h2:first-child,
    .docanalyzer-msg-bot h3:first-child,
    .docanalyzer-msg-bot h4:first-child {
      margin-top: 0;
    }
    .docanalyzer-msg-bot ul,
    .docanalyzer-msg-bot ol {
      margin: 0 0 8px 18px;
      padding-left: 0;
    }
    .docanalyzer-msg-bot li {
      margin-bottom: 4px;
    }
    .docanalyzer-msg-bot strong {
      font-weight: 700;
      color: #0f172a;
    }
    .docanalyzer-msg-bot hr {
      border: 0;
      border-top: 1px solid #e2e8f0;
      margin: 10px 0;
    }
    .docanalyzer-msg-bot code {
      background: #f1f5f9;
      padding: 2px 4px;
      border-radius: 4px;
      font-size: 0.82rem;
      font-family: monospace;
    }

    .docanalyzer-citations {
      margin-top: 10px;
      padding-top: 8px;
      border-top: 1px solid #e2e8f0;
      font-size: 0.74rem;
      color: #64748b;
    }

    .docanalyzer-badge {
      display: inline-block;
      background: #f1f5f9;
      padding: 3px 7px;
      border-radius: 5px;
      margin-top: 4px;
      margin-right: 4px;
      border: 1px solid #cbd5e1;
      font-weight: 500;
      color: #334155;
    }

    .docanalyzer-input-area {
      padding: 12px;
      background: #ffffff;
      border-top: 1px solid #e2e8f0;
      display: flex;
      gap: 8px;
    }

    .docanalyzer-input-area input {
      flex: 1;
      border: 1px solid #cbd5e1;
      border-radius: 20px;
      padding: 10px 16px;
      font-size: 0.9rem;
      outline: none;
      transition: border-color 0.2s;
    }

    .docanalyzer-input-area input:focus {
      border-color: #2563eb;
    }

    .docanalyzer-send-btn {
      background: #2563eb;
      color: white;
      border: none;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.2s;
    }

    .docanalyzer-send-btn:hover {
      background: #1d4ed8;
    }

    .docanalyzer-send-btn:disabled {
      background: #94a3b8;
      cursor: not-allowed;
    }

    /* Mobile Responsiveness for Phones & Small Screens */
    @media (max-width: 600px) {
      #docanalyzer-widget-container {
        bottom: 16px !important;
        right: 16px !important;
      }

      #docanalyzer-launcher {
        width: 52px !important;
        height: 52px !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4) !important;
      }

      #docanalyzer-launcher svg {
        width: 24px !important;
        height: 24px !important;
      }

      #docanalyzer-chat-window {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        width: 100% !important;
        width: 100vw !important;
        height: 100% !important;
        height: 100dvh !important;
        max-width: 100% !important;
        max-width: 100vw !important;
        max-height: 100% !important;
        max-height: 100dvh !important;
        border-radius: 0 !important;
        border: none !important;
        margin: 0 !important;
        z-index: 1000000 !important;
        box-shadow: none !important;
      }

      .docanalyzer-resizer {
        display: none !important;
      }

      #docanalyzer-expand {
        display: none !important;
      }

      .docanalyzer-header {
        padding: 14px 16px !important;
        border-radius: 0 !important;
      }

      .docanalyzer-header-title {
        font-size: 0.95rem !important;
      }

      .docanalyzer-header-sub {
        font-size: 0.72rem !important;
      }

      .docanalyzer-messages {
        padding: 12px !important;
        gap: 10px !important;
      }

      .docanalyzer-msg {
        max-width: 92% !important;
        padding: 10px 14px !important;
        font-size: 0.86rem !important;
        line-height: 1.5 !important;
      }

      .docanalyzer-input-area {
        padding: 10px 12px max(10px, env(safe-area-inset-bottom)) !important;
      }

      .docanalyzer-input-area input {
        font-size: 16px !important; /* Prevents auto-zoom on mobile iOS */
        padding: 9px 14px !important;
      }

      .docanalyzer-send-btn {
        width: 38px !important;
        height: 38px !important;
      }
    }
  `;
  document.head.appendChild(style);

  // Inject HTML Container
  const container = document.createElement('div');
  container.id = 'docanalyzer-widget-container';
  container.innerHTML = `
    <div id="docanalyzer-chat-window">
      <!-- Interactive Resize Handles -->
      <div class="docanalyzer-resizer docanalyzer-resizer-tl" id="docanalyzer-resize-tl" title="Drag to expand or shrink window size">
        <svg width="11" height="11" viewBox="0 0 11 11" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
          <line x1="2" y1="9" x2="9" y2="2"/>
          <line x1="5" y1="9" x2="9" y2="5"/>
        </svg>
      </div>
      <div class="docanalyzer-resizer docanalyzer-resizer-t" id="docanalyzer-resize-t" title="Drag to adjust height"></div>
      <div class="docanalyzer-resizer docanalyzer-resizer-l" id="docanalyzer-resize-l" title="Drag to adjust width"></div>

      <div class="docanalyzer-header">
        <div style="padding-left: 6px;">
          <div class="docanalyzer-header-title">Tech Industries Assistant</div>
          <div class="docanalyzer-header-sub">Ask about products, policies & services</div>
        </div>
        <div class="docanalyzer-header-controls">
          <button class="docanalyzer-icon-btn" id="docanalyzer-expand" title="Expand window size">
            <svg id="docanalyzer-expand-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>
            </svg>
          </button>
          <button class="docanalyzer-icon-btn" id="docanalyzer-close" title="Close chat">&times;</button>
        </div>
      </div>
      <div class="docanalyzer-messages" id="docanalyzer-msg-list">
        <div class="docanalyzer-msg docanalyzer-msg-bot">
          Hello! Welcome to Tech Industries. How can I assist you with our products, specifications, or company policies today?
        </div>
      </div>
      <form class="docanalyzer-input-area" id="docanalyzer-form">
        <input type="text" id="docanalyzer-input" placeholder="Type your message..." autocomplete="off" />
        <button type="submit" class="docanalyzer-send-btn" id="docanalyzer-submit">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
        </button>
      </form>
    </div>
    <button id="docanalyzer-launcher" title="Chat with Company Assistant">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
      </svg>
    </button>
  `;
  document.body.appendChild(container);

  // Logic & State
  let sessionId = sessionStorage.getItem('docanalyzer_widget_session_id') || null;
  const launcher = document.getElementById('docanalyzer-launcher');
  const chatWindow = document.getElementById('docanalyzer-chat-window');
  const expandBtn = document.getElementById('docanalyzer-expand');
  const expandIcon = document.getElementById('docanalyzer-expand-icon');
  const closeBtn = document.getElementById('docanalyzer-close');
  const form = document.getElementById('docanalyzer-form');
  const input = document.getElementById('docanalyzer-input');
  const msgList = document.getElementById('docanalyzer-msg-list');
  const submitBtn = document.getElementById('docanalyzer-submit');

  const expandSvg = '<path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>';
  const restoreSvg = '<path d="M4 14h6v6M20 10h-6V4M14 10l7-7M10 14l-7 7"/>';

  let isExpanded = false;
  let savedWidth = localStorage.getItem('docanalyzer_widget_width') || '400px';
  let savedHeight = localStorage.getItem('docanalyzer_widget_height') || '580px';

  // Apply saved custom size only on desktop screens (>600px)
  function applyWidgetDimensions() {
    if (window.innerWidth > 600) {
      if (localStorage.getItem('docanalyzer_widget_width')) {
        chatWindow.style.width = savedWidth;
      }
      if (localStorage.getItem('docanalyzer_widget_height')) {
        chatWindow.style.height = savedHeight;
      }
    } else {
      chatWindow.style.width = '';
      chatWindow.style.height = '';
    }
  }
  applyWidgetDimensions();
  window.addEventListener('resize', applyWidgetDimensions);

  launcher.addEventListener('click', () => {
    const isHidden = chatWindow.style.display === 'none' || !chatWindow.style.display;
    chatWindow.style.display = isHidden ? 'flex' : 'none';
    if (isHidden && window.innerWidth > 600) input.focus();
  });

  closeBtn.addEventListener('click', () => {
    chatWindow.style.display = 'none';
  });

  // Expand / Shrink toggle button
  expandBtn.addEventListener('click', () => {
    isExpanded = !isExpanded;
    if (isExpanded) {
      savedWidth = chatWindow.style.width || (chatWindow.offsetWidth + 'px');
      savedHeight = chatWindow.style.height || (chatWindow.offsetHeight + 'px');
      chatWindow.classList.add('docanalyzer-expanded');
      expandIcon.innerHTML = restoreSvg;
      expandBtn.title = 'Shrink / Restore size';
    } else {
      chatWindow.classList.remove('docanalyzer-expanded');
      chatWindow.style.width = savedWidth;
      chatWindow.style.height = savedHeight;
      expandIcon.innerHTML = expandSvg;
      expandBtn.title = 'Expand window size';
    }
  });

  // Flexible Drag-to-Resize Logic (NW corner, Top edge, Left edge)
  function setupResizer(handleEl, resizeType) {
    if (!handleEl) return;
    let startX, startY, startW, startH;

    function onMouseDown(e) {
      e.preventDefault();
      const clientX = e.clientX ?? (e.touches && e.touches[0].clientX);
      const clientY = e.clientY ?? (e.touches && e.touches[0].clientY);
      startX = clientX;
      startY = clientY;
      startW = chatWindow.offsetWidth;
      startH = chatWindow.offsetHeight;

      chatWindow.classList.add('docanalyzer-no-transition');
      if (isExpanded) {
        chatWindow.classList.remove('docanalyzer-expanded');
        isExpanded = false;
        expandIcon.innerHTML = expandSvg;
        expandBtn.title = 'Expand window size';
      }

      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
      document.addEventListener('touchmove', onMouseMove, { passive: false });
      document.addEventListener('touchend', onMouseUp);
      document.body.style.userSelect = 'none';
    }

    function onMouseMove(e) {
      const clientX = e.clientX ?? (e.touches && e.touches[0].clientX);
      const clientY = e.clientY ?? (e.touches && e.touches[0].clientY);
      const dx = clientX - startX;
      const dy = clientY - startY;

      const minW = 320;
      const maxW = window.innerWidth - 32;
      const minH = 380;
      const maxH = window.innerHeight - 90;

      if (resizeType === 'tl' || resizeType === 'l') {
        const newW = Math.min(Math.max(startW - dx, minW), maxW);
        chatWindow.style.width = newW + 'px';
      }
      if (resizeType === 'tl' || resizeType === 't') {
        const newH = Math.min(Math.max(startH - dy, minH), maxH);
        chatWindow.style.height = newH + 'px';
      }
    }

    function onMouseUp() {
      chatWindow.classList.remove('docanalyzer-no-transition');
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      document.removeEventListener('touchmove', onMouseMove);
      document.removeEventListener('touchend', onMouseUp);
      document.body.style.userSelect = '';

      // Persist custom size for subsequent sessions
      localStorage.setItem('docanalyzer_widget_width', chatWindow.style.width);
      localStorage.setItem('docanalyzer_widget_height', chatWindow.style.height);
      savedWidth = chatWindow.style.width;
      savedHeight = chatWindow.style.height;
    }

    handleEl.addEventListener('mousedown', onMouseDown);
    handleEl.addEventListener('touchstart', onMouseDown, { passive: false });
  }

  setupResizer(document.getElementById('docanalyzer-resize-tl'), 'tl');
  setupResizer(document.getElementById('docanalyzer-resize-t'), 't');
  setupResizer(document.getElementById('docanalyzer-resize-l'), 'l');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    // Append user message
    appendMsg('user', text);
    input.value = '';
    input.disabled = true;
    submitBtn.disabled = true;

    // Append typing placeholder
    const typing = document.createElement('div');
    typing.className = 'docanalyzer-msg docanalyzer-msg-bot';
    typing.innerText = 'Thinking...';
    msgList.appendChild(typing);
    msgList.scrollTop = msgList.scrollHeight;

    try {
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });
      const data = await res.json();
      typing.remove();

      if (res.ok) {
        sessionId = data.session_id;
        sessionStorage.setItem('docanalyzer_widget_session_id', sessionId);
        appendMsg('bot', data.answer, data.sources);
      } else {
        appendMsg('bot', 'Sorry, an error occurred. Please try again.');
      }
    } catch (err) {
      typing.remove();
      appendMsg('bot', 'Could not reach server. Is the backend running?');
    } finally {
      input.disabled = false;
      submitBtn.disabled = false;
      input.focus();
      msgList.scrollTop = msgList.scrollHeight;
    }
  });

  function renderMarkdown(text) {
    if (window.marked && typeof window.marked.parse === 'function') {
      return window.marked.parse(text);
    }
    // Fallback lightweight regex formatter
    return text
      .replace(/^### (.*$)/gim, '<h4>$1</h4>')
      .replace(/^## (.*$)/gim, '<h3>$1</h3>')
      .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
      .replace(/^\* (.*$)/gim, '<li>$1</li>')
      .replace(/\n\n+/g, '<br><br>')
      .replace(/\n/g, '<br>');
  }

  function appendMsg(role, content, sources = []) {
    const div = document.createElement('div');
    div.className = `docanalyzer-msg docanalyzer-msg-${role}`;

    if (role === 'bot') {
      div.innerHTML = renderMarkdown(content);
    } else {
      div.textContent = content;
    }

    if (role === 'bot' && sources && sources.length > 0) {
      const citeDiv = document.createElement('div');
      citeDiv.className = 'docanalyzer-citations';
      citeDiv.innerText = 'Sources:';
      
      const seen = new Set();
      sources.forEach((s) => {
        const file = s.source.split(/[\\\\/]/).pop();
        const key = `${file}-${s.page}`;
        if (!seen.has(key)) {
          seen.add(key);
          const badge = document.createElement('span');
          badge.className = 'docanalyzer-badge';
          badge.innerText = `📄 ${file} (p.${s.page})`;
          citeDiv.appendChild(badge);
        }
      });
      div.appendChild(citeDiv);
    }

    msgList.appendChild(div);
    msgList.scrollTop = msgList.scrollHeight;
  }
})();
