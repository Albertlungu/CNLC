import { sendAgentMessage, requireAuth, logout, getSession } from "./api-client.js";
import { initNavbar } from "./components/navbar.js";

if (!requireAuth()) {
    throw new Error("Authentication required");
}
initNavbar("agent");

const session = getSession();
const userId = session.userId;

const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const typingIndicator = document.getElementById("typing-indicator");
const welcomeState = document.getElementById("welcome-state");
const suggestionChips = document.getElementById("suggestion-chips");
const chatListEl = document.getElementById("chat-list");
const newChatBtn = document.getElementById("new-chat-btn");
const sidebarToggle = document.getElementById("sidebar-toggle");
const chatSidebar = document.getElementById("chat-sidebar");

// ==================== Multi-chat storage ====================

const CHATS_INDEX_KEY = `discovereye-chats-${userId}`;
const ACTIVE_CHAT_KEY = `discovereye-active-chat-${userId}`;

// Each chat: { id, title, agentSessionId, updatedAt }
// Messages stored at: discovereye-chat-msgs-{chatId}

let chatsIndex = []; // sorted newest first
let activeChatId = null;
let agentSessionId = null;
let isProcessing = false;
let chatHistory = [];

function loadChatsIndex() {
    try {
        const raw = localStorage.getItem(CHATS_INDEX_KEY);
        chatsIndex = raw ? JSON.parse(raw) : [];
    } catch (e) {
        chatsIndex = [];
    }
}

function saveChatsIndex() {
    try {
        localStorage.setItem(CHATS_INDEX_KEY, JSON.stringify(chatsIndex));
    } catch (e) {}
}

function migrateOldHistory() {
    // Migrate from old single-chat storage to new multi-chat format
    const oldHistoryKey = `discovereye-agent-history-${userId}`;
    const oldSessionKey = `discovereye-agent-session-${userId}`;
    const oldHistory = localStorage.getItem(oldHistoryKey);
    const oldSession = localStorage.getItem(oldSessionKey);

    if (!oldHistory) return;

    try {
        const entries = JSON.parse(oldHistory);
        if (entries.length === 0) return;

        // Create a chat from old data
        const chatId = oldSession || crypto.randomUUID();
        const firstUserMsg = entries.find(e => e.sender === "user");
        const title = firstUserMsg ? firstUserMsg.text.slice(0, 50) : "Previous chat";

        const chat = {
            id: chatId,
            title,
            agentSessionId: oldSession || null,
            updatedAt: new Date().toISOString(),
        };

        localStorage.setItem(`discovereye-chat-msgs-${chatId}`, JSON.stringify(entries));
        chatsIndex.push(chat);
        saveChatsIndex();

        // Clean up old keys
        localStorage.removeItem(oldHistoryKey);
        localStorage.removeItem(oldSessionKey);
    } catch (e) {}
}

function loadChatMessages(chatId) {
    try {
        const raw = localStorage.getItem(`discovereye-chat-msgs-${chatId}`);
        return raw ? JSON.parse(raw) : [];
    } catch (e) {
        return [];
    }
}

function saveChatMessages(chatId, messages) {
    try {
        localStorage.setItem(`discovereye-chat-msgs-${chatId}`, JSON.stringify(messages));
    } catch (e) {
        if (messages.length > 20) {
            const trimmed = messages.slice(-20);
            try { localStorage.setItem(`discovereye-chat-msgs-${chatId}`, JSON.stringify(trimmed)); } catch (_) {}
        }
    }
}

function saveHistory() {
    if (!activeChatId) return;
    saveChatMessages(activeChatId, chatHistory);

    // Update the chat index entry
    const chat = chatsIndex.find(c => c.id === activeChatId);
    if (chat) {
        chat.agentSessionId = agentSessionId;
        chat.updatedAt = new Date().toISOString();
        if (!chat.title || chat.title === "New chat") {
            const firstUser = chatHistory.find(e => e.sender === "user");
            if (firstUser) chat.title = firstUser.text.slice(0, 50);
        }
        saveChatsIndex();
    }

    localStorage.setItem(ACTIVE_CHAT_KEY, activeChatId);
    renderChatList();
}

function deleteChat(chatId) {
    chatsIndex = chatsIndex.filter(c => c.id !== chatId);
    saveChatsIndex();
    localStorage.removeItem(`discovereye-chat-msgs-${chatId}`);

    if (activeChatId === chatId) {
        if (chatsIndex.length > 0) {
            switchToChat(chatsIndex[0].id);
        } else {
            startNewChat();
        }
    } else {
        renderChatList();
    }
}

// ==================== Welcome state ====================

function showWelcome() {
    if (welcomeState) {
        welcomeState.style.display = "";
    }
}

function hideWelcome() {
    if (welcomeState) {
        welcomeState.style.display = "none";
    }
}

if (suggestionChips) {
    suggestionChips.addEventListener("click", (e) => {
        const chip = e.target.closest(".chip");
        if (chip && chip.dataset.message) {
            handleSend(chip.dataset.message);
        }
    });
}

// ==================== Message rendering ====================

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function renderTextMessage(text, sender) {
    const msg = document.createElement("div");
    msg.className = `message ${sender}-message`;

    if (sender === "agent" && window.marked) {
        const html = window.marked.parse(text);
        msg.innerHTML = `<div class="message-content markdown-body">${html}</div>`;
    } else {
        let html = escapeHtml(text);
        html = html.replace(/\n/g, "<br>");
        msg.innerHTML = `<div class="message-content"><p>${html}</p></div>`;
    }

    return msg;
}

function renderBusinessCard(business) {
    const card = document.createElement("div");
    card.className = "inline-card";

    const addr = business.address;
    let addressText = "";
    if (addr && typeof addr === "object") {
        const parts = [];
        if (addr.housenumber) parts.push(addr.housenumber);
        if (addr.street) parts.push(addr.street);
        if (addr.city) parts.push(addr.city);
        addressText = parts.join(" ");
    }

    let imageHtml = "";
    if (business.image_url) {
        imageHtml = `<img class="inline-card-image" src="${escapeHtml(business.image_url)}" alt="" onerror="this.style.display='none'" loading="lazy">`;
    }

    card.innerHTML = `
        ${imageHtml}
        <div class="inline-card-name">${escapeHtml(business.name || "")}</div>
        ${addressText ? `<div class="inline-card-meta">${escapeHtml(addressText)}</div>` : ""}
        ${business.category ? `<span class="inline-card-category">${escapeHtml(business.category)}</span>` : ""}
    `;

    if (business.id) {
        card.addEventListener("click", () => {
            window.open(`business-detail.html?id=${business.id}`, "_blank");
        });
    }

    return card;
}

function renderReservationCard(reservation) {
    const card = document.createElement("div");
    card.className = "reservation-card";
    card.innerHTML = `
        <div class="reservation-card-title">Reservation Confirmed</div>
        <div class="reservation-card-detail">${escapeHtml(reservation.businessName || "")}</div>
        <div class="reservation-card-detail">${escapeHtml(reservation.date || "")} at ${escapeHtml(reservation.time || "")} - Party of ${reservation.partySize || "?"}</div>
        <div class="reservation-card-detail">Status: ${escapeHtml(reservation.status || "confirmed")}</div>
    `;
    return card;
}

function renderDealCard(deal) {
    const card = document.createElement("div");
    card.className = "deal-card";
    let discount = deal.discountType || "";
    if (deal.discountValue) {
        discount = deal.discountType === "percentage" ? `${deal.discountValue}% off` : `$${deal.discountValue} off`;
    }
    card.innerHTML = `
        <div class="deal-card-title">${escapeHtml(deal.title || "Deal")}</div>
        ${discount ? `<div class="deal-card-detail">${escapeHtml(discount)}</div>` : ""}
        ${deal.description ? `<div class="deal-card-detail">${escapeHtml(deal.description)}</div>` : ""}
        ${deal.expiresAt ? `<div class="deal-card-detail">Expires: ${escapeHtml(deal.expiresAt)}</div>` : ""}
    `;
    return card;
}

function renderCards(cards) {
    if (!cards || cards.length === 0) return null;

    const grid = document.createElement("div");
    grid.className = "card-grid";

    for (const card of cards) {
        if (card.type === "business" && card.data) {
            grid.appendChild(renderBusinessCard(card.data));
        } else if (card.type === "reservation" && card.data) {
            grid.appendChild(renderReservationCard(card.data));
        } else if (card.type === "deal" && card.data) {
            grid.appendChild(renderDealCard(card.data));
        }
    }

    return grid.children.length > 0 ? grid : null;
}

function renderErrorMessage(text, retryCallback) {
    const msg = document.createElement("div");
    msg.className = "error-bubble";
    msg.textContent = text;

    if (retryCallback) {
        const btn = document.createElement("button");
        btn.className = "retry-btn";
        btn.textContent = "Retry";
        btn.addEventListener("click", retryCallback);
        msg.appendChild(btn);
    }

    return msg;
}

function appendToChat(element) {
    chatMessages.appendChild(element);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ==================== Render chat messages ====================

function clearChatArea() {
    // Remove all children except the welcome state
    const children = Array.from(chatMessages.children);
    for (const child of children) {
        if (child !== welcomeState) {
            child.remove();
        }
    }
}

function renderMessagesFromHistory(entries) {
    for (const entry of entries) {
        if (entry.type === "text") {
            appendToChat(renderTextMessage(entry.text, entry.sender));
        } else if (entry.type === "business_card" && entry.data) {
            const wrapper = document.createElement("div");
            wrapper.className = "message agent-message";
            const grid = document.createElement("div");
            grid.className = "card-grid";
            grid.appendChild(renderBusinessCard(entry.data));
            wrapper.appendChild(grid);
            appendToChat(wrapper);
        } else if (entry.type === "cards" && entry.data) {
            const cardGrid = renderCards(entry.data);
            if (cardGrid) {
                const wrapper = document.createElement("div");
                wrapper.className = "message agent-message";
                wrapper.appendChild(cardGrid);
                appendToChat(wrapper);
            }
        }
    }
}

// ==================== Chat switching ====================

function switchToChat(chatId) {
    const chat = chatsIndex.find(c => c.id === chatId);
    if (!chat) return;

    activeChatId = chatId;
    agentSessionId = chat.agentSessionId || null;
    chatHistory = loadChatMessages(chatId);

    localStorage.setItem(ACTIVE_CHAT_KEY, chatId);

    clearChatArea();

    if (chatHistory.length > 0) {
        hideWelcome();
        renderMessagesFromHistory(chatHistory);
    } else {
        showWelcome();
    }

    renderChatList();
    chatInput.focus();
}

function startNewChat() {
    const chatId = crypto.randomUUID();
    const chat = {
        id: chatId,
        title: "New chat",
        agentSessionId: null,
        updatedAt: new Date().toISOString(),
    };

    chatsIndex.unshift(chat);
    saveChatsIndex();

    activeChatId = chatId;
    agentSessionId = null;
    chatHistory = [];

    localStorage.setItem(ACTIVE_CHAT_KEY, chatId);

    clearChatArea();
    showWelcome();
    renderChatList();
    chatInput.focus();
}

// ==================== Sidebar rendering ====================

function formatRelativeDate(isoStr) {
    const d = new Date(isoStr);
    const now = new Date();
    const diffMs = now - d;
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return "Just now";
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    const diffDay = Math.floor(diffHr / 24);
    if (diffDay < 7) return `${diffDay}d ago`;
    return d.toLocaleDateString();
}

function renderChatList() {
    chatListEl.innerHTML = "";

    if (chatsIndex.length === 0) {
        chatListEl.innerHTML = `<div class="chat-list-empty">No conversations yet</div>`;
        return;
    }

    // Sort newest first
    const sorted = [...chatsIndex].sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));

    for (const chat of sorted) {
        const item = document.createElement("div");
        item.className = `chat-list-item${chat.id === activeChatId ? " active" : ""}`;

        const textDiv = document.createElement("div");
        textDiv.className = "chat-list-item-text";

        const titleDiv = document.createElement("div");
        titleDiv.className = "chat-list-item-title";
        titleDiv.textContent = chat.title || "New chat";

        const dateDiv = document.createElement("div");
        dateDiv.className = "chat-list-item-date";
        dateDiv.textContent = formatRelativeDate(chat.updatedAt);

        textDiv.appendChild(titleDiv);
        textDiv.appendChild(dateDiv);

        const deleteBtn = document.createElement("button");
        deleteBtn.className = "chat-list-item-delete";
        deleteBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
        deleteBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            deleteChat(chat.id);
        });

        item.appendChild(textDiv);
        item.appendChild(deleteBtn);

        item.addEventListener("click", () => {
            switchToChat(chat.id);
            // Close sidebar on mobile
            if (chatSidebar) chatSidebar.classList.remove("open");
        });

        chatListEl.appendChild(item);
    }
}

// ==================== Interleaved card rendering ====================

function renderInterleavedResponse(message, cards, businessMap) {
    const cardMarkerRegex = /\{\{CARD:(\d+)\}\}/g;
    const hasMarkers = cardMarkerRegex.test(message);

    if (hasMarkers && Object.keys(businessMap).length > 0) {
        const usedBusinessIds = new Set();
        const segments = message.split(/\{\{CARD:(\d+)\}\}/);

        for (let i = 0; i < segments.length; i++) {
            if (i % 2 === 0) {
                const txt = segments[i].trim();
                if (txt) {
                    appendToChat(renderTextMessage(txt, "agent"));
                    recordEntry({ type: "text", sender: "agent", text: txt });
                }
            } else {
                const bizId = segments[i];
                const bizData = businessMap[bizId];
                if (bizData) {
                    usedBusinessIds.add(bizId);
                    const wrapper = document.createElement("div");
                    wrapper.className = "message agent-message";
                    const grid = document.createElement("div");
                    grid.className = "card-grid";
                    grid.appendChild(renderBusinessCard(bizData));
                    wrapper.appendChild(grid);
                    appendToChat(wrapper);
                    recordEntry({ type: "business_card", data: bizData });
                }
            }
        }

        const remainingCards = cards.filter(c => {
            if (c.type === "business") {
                return !usedBusinessIds.has(String(c.data && c.data.id));
            }
            return c.type === "reservation" || c.type === "deal";
        }).filter(c => c.type !== "business");

        if (remainingCards.length > 0) {
            const leftoverGrid = renderCards(remainingCards);
            if (leftoverGrid) {
                const wrapper = document.createElement("div");
                wrapper.className = "message agent-message";
                wrapper.appendChild(leftoverGrid);
                appendToChat(wrapper);
                recordEntry({ type: "cards", data: remainingCards });
            }
        }
    } else {
        if (message) {
            appendToChat(renderTextMessage(message, "agent"));
            recordEntry({ type: "text", sender: "agent", text: message });
        }

        if (cards.length > 0) {
            const cardGrid = renderCards(cards);
            if (cardGrid) {
                const wrapper = document.createElement("div");
                wrapper.className = "message agent-message";
                wrapper.appendChild(cardGrid);
                appendToChat(wrapper);
                recordEntry({ type: "cards", data: cards });
            }
        }
    }

    saveHistory();
}

// ==================== Chat logic ====================

function recordEntry(entry) {
    chatHistory.push(entry);
}

const TYPING_ORIGINAL_TEXT = "Agent is thinking...";

function setTypingStatus(text) {
    typingIndicator.style.display = "flex";
    const lastChild = typingIndicator.lastChild;
    if (lastChild && lastChild.nodeType === Node.TEXT_NODE) {
        lastChild.textContent = text;
    }
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function handleSend(messageText) {
    if (isProcessing || !messageText.trim()) return;

    const text = messageText.trim();
    isProcessing = true;
    sendBtn.disabled = true;
    chatInput.value = "";

    hideWelcome();

    // If no active chat yet, create one
    if (!activeChatId) {
        startNewChat();
    }

    // Render and record user message
    appendToChat(renderTextMessage(text, "user"));
    chatHistory.push({ type: "text", sender: "user", text });
    saveHistory();

    setTypingStatus(TYPING_ORIGINAL_TEXT);

    try {
        const res = await sendAgentMessage(userId, text, agentSessionId);

        typingIndicator.style.display = "none";

        if (res.sessionId) {
            agentSessionId = res.sessionId;
        }

        const message = res.message || "";
        const cards = res.cards || [];
        const businessMap = res.businessMap || {};

        renderInterleavedResponse(message, cards, businessMap);
    } catch (err) {
        typingIndicator.style.display = "none";

        if (err && err.status === 429) {
            const seconds = err.retryAfter || 60;
            appendToChat(renderErrorMessage(`Please wait ${seconds}s before sending another message.`));
        } else if (err && err.message) {
            appendToChat(renderErrorMessage(err.message, () => handleSend(text)));
        } else {
            appendToChat(renderErrorMessage("Something went wrong. Please try again.", () => handleSend(text)));
        }
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

// ==================== Event listeners ====================

chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    handleSend(chatInput.value);
});

newChatBtn.addEventListener("click", () => {
    startNewChat();
    if (chatSidebar) chatSidebar.classList.remove("open");
});

if (sidebarToggle && chatSidebar) {
    sidebarToggle.addEventListener("click", () => {
        chatSidebar.classList.toggle("open");
    });
}

// ==================== Init ====================

loadChatsIndex();
migrateOldHistory();

// Restore last active chat or show welcome
const lastActiveId = localStorage.getItem(ACTIVE_CHAT_KEY);
if (lastActiveId && chatsIndex.find(c => c.id === lastActiveId)) {
    switchToChat(lastActiveId);
} else if (chatsIndex.length > 0) {
    const sorted = [...chatsIndex].sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
    switchToChat(sorted[0].id);
} else {
    renderChatList();
}

chatInput.focus();
