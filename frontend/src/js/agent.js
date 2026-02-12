import { sendAgentMessage, requireAuth, logout, getSession } from "./api-client.js";

if (!requireAuth()) {
    throw new Error("Authentication required");
}

const session = getSession();
const userId = session.userId;

const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const typingIndicator = document.getElementById("typing-indicator");
const logoutBtn = document.getElementById("logout-btn");
const welcomeState = document.getElementById("welcome-state");
const suggestionChips = document.getElementById("suggestion-chips");

let agentSessionId = null;
let isProcessing = false;

// ==================== Welcome state ====================

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

    // Convert markdown-style formatting
    let html = escapeHtml(text);
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\n/g, "<br>");

    msg.innerHTML = `<div class="message-content"><p>${html}</p></div>`;
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

// ==================== Chat logic ====================

async function handleSend(messageText) {
    if (isProcessing || !messageText.trim()) return;

    const text = messageText.trim();
    isProcessing = true;
    sendBtn.disabled = true;
    chatInput.value = "";

    // Hide welcome state on first message
    hideWelcome();

    // Render user message
    appendToChat(renderTextMessage(text, "user"));

    // Show typing
    typingIndicator.style.display = "flex";
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const result = await sendAgentMessage(userId, text, agentSessionId);

        // Store session ID
        if (result.sessionId) {
            agentSessionId = result.sessionId;
        }

        // Validate response
        const message = result.message || "";
        const cards = Array.isArray(result.cards) ? result.cards : [];
        const businessMap = result.businessMap || {};

        // Check if the message contains {{CARD:id}} markers for interleaved rendering
        const cardMarkerRegex = /\{\{CARD:(\d+)\}\}/g;
        const hasMarkers = cardMarkerRegex.test(message);

        if (hasMarkers && Object.keys(businessMap).length > 0) {
            // Interleaved rendering: split text on markers, render text + card alternating
            const usedBusinessIds = new Set();
            const segments = message.split(/\{\{CARD:(\d+)\}\}/);

            // segments alternates: [text, id, text, id, text, ...]
            for (let i = 0; i < segments.length; i++) {
                if (i % 2 === 0) {
                    // Text segment
                    const txt = segments[i].trim();
                    if (txt) {
                        appendToChat(renderTextMessage(txt, "agent"));
                    }
                } else {
                    // Business ID segment -- render the card
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
                    }
                }
            }

            // Render any remaining non-business cards (reservations, deals) that weren't inline
            const remainingCards = cards.filter(c => {
                if (c.type === "business") {
                    return !usedBusinessIds.has(String(c.data && c.data.id));
                }
                return c.type === "reservation" || c.type === "deal";
            }).filter(c => c.type !== "business"); // only non-business leftovers

            const leftoverGrid = renderCards(remainingCards);
            if (leftoverGrid) {
                const wrapper = document.createElement("div");
                wrapper.className = "message agent-message";
                wrapper.appendChild(leftoverGrid);
                appendToChat(wrapper);
            }
        } else {
            // Fallback: no markers, render text then all cards (original behavior)
            if (message) {
                appendToChat(renderTextMessage(message, "agent"));
            }

            const cardGrid = renderCards(cards);
            if (cardGrid) {
                const wrapper = document.createElement("div");
                wrapper.className = "message agent-message";
                wrapper.appendChild(cardGrid);
                appendToChat(wrapper);
            }
        }

    } catch (err) {
        if (err && err.status === 429) {
            const seconds = err.retryAfter || 60;
            appendToChat(renderErrorMessage(`Please wait ${seconds}s before sending another message.`));
        } else if (err && err.message) {
            appendToChat(renderErrorMessage(err.message, () => handleSend(text)));
        } else {
            appendToChat(renderErrorMessage("Connection lost. Please try again.", () => handleSend(text)));
        }
    } finally {
        typingIndicator.style.display = "none";
        isProcessing = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    handleSend(chatInput.value);
});

if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
        e.preventDefault();
        logout();
    });
}

chatInput.focus();
