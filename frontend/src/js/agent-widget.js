import { sendAgentMessage, isLoggedIn, getSession } from "./api-client.js";

if (!isLoggedIn()) {
    // Don't render widget for unauthenticated users
} else {
    initWidget();
}

function initWidget() {
    const session = getSession();
    const userId = session.userId;

    let agentSessionId = null;
    let isProcessing = false;
    let isOpen = false;

    // ==================== Build DOM ====================

    const widget = document.createElement("div");
    widget.id = "agent-widget";
    widget.innerHTML = `
        <button class="agent-widget-fab" id="agent-widget-fab" aria-label="Open AI assistant">
            <svg class="agent-widget-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <svg class="agent-widget-close-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none;">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
        </button>
        <div class="agent-widget-panel" id="agent-widget-panel">
            <div class="agent-widget-header">
                <div class="agent-widget-header-left">
                    <div class="agent-widget-avatar">AI</div>
                    <div>
                        <div class="agent-widget-title">Discovereye Assistant</div>
                        <div class="agent-widget-status">Online</div>
                    </div>
                </div>
                <a href="agent.html" class="agent-widget-expand" title="Open full view">
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="15 3 21 3 21 9"></polyline>
                        <polyline points="9 21 3 21 3 15"></polyline>
                        <line x1="21" y1="3" x2="14" y2="10"></line>
                        <line x1="3" y1="21" x2="10" y2="14"></line>
                    </svg>
                </a>
            </div>
            <div class="agent-widget-messages" id="agent-widget-messages">
                <div class="agent-widget-msg agent-widget-msg-agent">
                    <div class="agent-widget-msg-content">Hi! I'm the Discovereye assistant. How can I help you today?</div>
                </div>
            </div>
            <div class="agent-widget-typing" id="agent-widget-typing" style="display:none;">
                <span></span><span></span><span></span>
            </div>
            <form class="agent-widget-input" id="agent-widget-form">
                <input type="text" id="agent-widget-input" placeholder="Ask me anything..." autocomplete="off" maxlength="2000">
                <button type="submit" id="agent-widget-send" aria-label="Send message">
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                </button>
            </form>
        </div>
    `;
    document.body.appendChild(widget);

    // ==================== References ====================

    const fab = document.getElementById("agent-widget-fab");
    const panel = document.getElementById("agent-widget-panel");
    const messages = document.getElementById("agent-widget-messages");
    const form = document.getElementById("agent-widget-form");
    const input = document.getElementById("agent-widget-input");
    const sendBtn = document.getElementById("agent-widget-send");
    const typing = document.getElementById("agent-widget-typing");
    const chatIcon = widget.querySelector(".agent-widget-icon");
    const closeIcon = widget.querySelector(".agent-widget-close-icon");

    // ==================== Toggle ====================

    fab.addEventListener("click", () => {
        isOpen = !isOpen;
        panel.classList.toggle("open", isOpen);
        fab.classList.toggle("active", isOpen);
        chatIcon.style.display = isOpen ? "none" : "block";
        closeIcon.style.display = isOpen ? "block" : "none";
        if (isOpen) {
            input.focus();
        }
    });

    // ==================== Helpers ====================

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function appendMessage(text, sender) {
        const msg = document.createElement("div");
        msg.className = `agent-widget-msg agent-widget-msg-${sender}`;

        let html = escapeHtml(text);
        html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        html = html.replace(/\n/g, "<br>");

        msg.innerHTML = `<div class="agent-widget-msg-content">${html}</div>`;
        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
    }

    function appendError(text) {
        const msg = document.createElement("div");
        msg.className = "agent-widget-msg agent-widget-msg-error";
        msg.innerHTML = `<div class="agent-widget-msg-content">${escapeHtml(text)}</div>`;
        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
    }

    // ==================== Send ====================

    async function handleSend(text) {
        if (isProcessing || !text.trim()) return;

        const trimmed = text.trim();
        isProcessing = true;
        sendBtn.disabled = true;
        input.value = "";

        appendMessage(trimmed, "user");

        typing.style.display = "flex";
        messages.scrollTop = messages.scrollHeight;

        try {
            const result = await sendAgentMessage(userId, trimmed, agentSessionId);

            if (result.sessionId) {
                agentSessionId = result.sessionId;
            }

            const message = result.message || "";
            if (message) {
                appendMessage(message, "agent");
            }

            // Show card summaries as text in the widget (no full card rendering)
            const cards = Array.isArray(result.cards) ? result.cards : [];
            if (cards.length > 0 && !message) {
                appendMessage(`Found ${cards.length} result(s). Open the full view to see details.`, "agent");
            }
        } catch (err) {
            if (err && err.status === 429) {
                const seconds = err.retryAfter || 60;
                appendError(`Please wait ${seconds}s before sending another message.`);
            } else if (err && err.message) {
                appendError(err.message);
            } else {
                appendError("Connection lost. Please try again.");
            }
        } finally {
            typing.style.display = "none";
            isProcessing = false;
            sendBtn.disabled = false;
            input.focus();
        }
    }

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        handleSend(input.value);
    });
}
