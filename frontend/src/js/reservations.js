import {
    requireAuth, getSession, logout,
    filterBusinesses,
    createReservation, getUserReservations, cancelReservation, downloadICS,
    getNotifications, markNotificationRead, markAllNotificationsRead, checkReminders,
} from "./api-client.js";

if (!requireAuth()) throw new Error("Not authenticated");

const session = getSession();
const userId = session.userId;

// Logout
document.getElementById("logout-btn").addEventListener("click", (e) => {
    e.preventDefault();
    logout();
});

// ==================== Tabs ====================
const tabBtns = document.querySelectorAll(".tab-btn");
tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
        tabBtns.forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
        btn.classList.add("active");
        document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
        if (btn.dataset.tab === "calendar") renderCalendar();
    });
});

// ==================== Load Reservations ====================
let allReservations = [];

async function loadReservations() {
    try {
        const result = await getUserReservations(userId);
        if (result.status === "success") {
            allReservations = result.reservations;
            renderUpcoming();
            renderAll();
        }
    } catch (err) {
        console.error("Error loading reservations:", err);
    }
}

function renderReservationCard(r) {
    const card = document.createElement("div");
    card.className = `reservation-card ${r.status}`;
    const statusClass = r.status;

    card.innerHTML = `
        <div class="reservation-info">
            <h3>${r.businessName || "Business"}</h3>
            <div class="reservation-details">
                <span>${r.date}</span>
                <span>${r.time}</span>
                <span>${r.partySize} guest${r.partySize > 1 ? "s" : ""}</span>
            </div>
            ${r.notes ? `<div class="reservation-details"><span>${r.notes}</span></div>` : ""}
            <span class="reservation-status ${statusClass}">${r.status}</span>
        </div>
        <div class="reservation-actions">
            <button class="btn-ics" data-id="${r.reservationId}">Add to Calendar</button>
            ${r.status === "confirmed" ? `<button class="btn-cancel" data-id="${r.reservationId}">Cancel</button>` : ""}
        </div>
    `;

    card.querySelector(".btn-ics").addEventListener("click", () => downloadICS(r.reservationId));
    const cancelBtn = card.querySelector(".btn-cancel");
    if (cancelBtn) {
        cancelBtn.addEventListener("click", async () => {
            if (!confirm("Cancel this reservation?")) return;
            const result = await cancelReservation(r.reservationId, userId);
            if (result.status === "success") loadReservations();
            else alert(result.message || "Failed to cancel");
        });
    }

    return card;
}

function renderUpcoming() {
    const container = document.getElementById("upcoming-list");
    const now = new Date().toISOString().slice(0, 10);
    const upcoming = allReservations.filter(r => r.status === "confirmed" && r.date >= now);
    upcoming.sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time));

    if (upcoming.length === 0) {
        container.innerHTML = `<div class="no-reservations">No upcoming reservations. Make one!</div>`;
        return;
    }
    container.innerHTML = "";
    upcoming.forEach(r => container.appendChild(renderReservationCard(r)));
}

function renderAll() {
    const container = document.getElementById("all-list");
    if (allReservations.length === 0) {
        container.innerHTML = `<div class="no-reservations">No reservations yet.</div>`;
        return;
    }
    container.innerHTML = "";
    const sorted = [...allReservations].sort((a, b) => (b.date + b.time).localeCompare(a.date + a.time));
    sorted.forEach(r => container.appendChild(renderReservationCard(r)));
}

// ==================== Calendar ====================
let calendarYear, calendarMonth;

function initCalendar() {
    const now = new Date();
    calendarYear = now.getFullYear();
    calendarMonth = now.getMonth();
}

function renderCalendar() {
    const title = document.getElementById("calendar-title");
    const grid = document.getElementById("calendar-grid");
    const months = ["January","February","March","April","May","June","July","August","September","October","November","December"];
    title.textContent = `${months[calendarMonth]} ${calendarYear}`;

    grid.innerHTML = "";
    const dayNames = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
    dayNames.forEach(d => {
        const cell = document.createElement("div");
        cell.className = "calendar-header-cell";
        cell.textContent = d;
        grid.appendChild(cell);
    });

    const firstDay = new Date(calendarYear, calendarMonth, 1).getDay();
    const daysInMonth = new Date(calendarYear, calendarMonth + 1, 0).getDate();
    const today = new Date();

    for (let i = 0; i < firstDay; i++) {
        const cell = document.createElement("div");
        cell.className = "calendar-cell empty";
        grid.appendChild(cell);
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const cell = document.createElement("div");
        cell.className = "calendar-cell";
        const dateStr = `${calendarYear}-${String(calendarMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;

        if (today.getFullYear() === calendarYear && today.getMonth() === calendarMonth && today.getDate() === day) {
            cell.classList.add("today");
        }

        cell.innerHTML = `<div class="day-number">${day}</div>`;

        const dayReservations = allReservations.filter(r => r.date === dateStr && r.status === "confirmed");
        dayReservations.forEach(r => {
            const event = document.createElement("div");
            event.className = "calendar-event";
            event.textContent = `${r.time} ${r.businessName || ""}`.trim();
            event.title = `${r.businessName} - ${r.time} - ${r.partySize} guests`;
            cell.appendChild(event);
        });

        grid.appendChild(cell);
    }
}

initCalendar();

document.getElementById("prev-month").addEventListener("click", () => {
    calendarMonth--;
    if (calendarMonth < 0) { calendarMonth = 11; calendarYear--; }
    renderCalendar();
});

document.getElementById("next-month").addEventListener("click", () => {
    calendarMonth++;
    if (calendarMonth > 11) { calendarMonth = 0; calendarYear++; }
    renderCalendar();
});

// ==================== New Reservation Modal ====================
const modal = document.getElementById("reservation-modal");
const newBtn = document.getElementById("new-reservation-btn");
const closeBtn = document.getElementById("reservation-close");

newBtn.addEventListener("click", () => modal.classList.add("active"));
closeBtn.addEventListener("click", () => modal.classList.remove("active"));
modal.addEventListener("click", (e) => { if (e.target === modal) modal.classList.remove("active"); });

// Business search in modal
const searchInput = document.getElementById("res-business-search");
const searchResults = document.getElementById("res-search-results");
let searchTimeout = null;

searchInput.addEventListener("input", () => {
    clearTimeout(searchTimeout);
    const query = searchInput.value.trim();
    if (query.length < 2) { searchResults.classList.remove("active"); return; }
    searchTimeout = setTimeout(async () => {
        try {
            const result = await filterBusinesses(query, null, null, null, null, null, 0, 10);
            if (result.businesses && result.businesses.length > 0) {
                searchResults.innerHTML = result.businesses.map(b =>
                    `<div class="search-dropdown-item" data-id="${b.id}" data-name="${b.name}">${b.name}${b.category ? ` (${b.category})` : ""}</div>`
                ).join("");
                searchResults.classList.add("active");
                searchResults.querySelectorAll(".search-dropdown-item").forEach(item => {
                    item.addEventListener("click", () => {
                        document.getElementById("res-business-id").value = item.dataset.id;
                        document.getElementById("res-business-name").value = item.dataset.name;
                        searchInput.value = item.dataset.name;
                        searchResults.classList.remove("active");
                    });
                });
            } else {
                searchResults.innerHTML = `<div class="search-dropdown-item">No results found</div>`;
                searchResults.classList.add("active");
            }
        } catch (err) {
            console.error("Search error:", err);
        }
    }, 300);
});

// Set min date to today
document.getElementById("res-date").min = new Date().toISOString().slice(0, 10);

// Form submit
document.getElementById("reservation-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const businessId = parseInt(document.getElementById("res-business-id").value);
    const businessName = document.getElementById("res-business-name").value;
    const date = document.getElementById("res-date").value;
    const time = document.getElementById("res-time").value;
    const partySize = parseInt(document.getElementById("res-party-size").value);
    const notes = document.getElementById("res-notes").value || null;

    if (!businessId) { alert("Please select a business."); return; }

    try {
        const result = await createReservation(userId, businessId, businessName, date, time, partySize, notes);
        if (result.status === "success") {
            modal.classList.remove("active");
            document.getElementById("reservation-form").reset();
            document.getElementById("res-business-id").value = "";
            document.getElementById("res-business-name").value = "";
            loadReservations();
            loadNotifications();
        } else {
            alert(result.message || "Failed to create reservation");
        }
    } catch (err) {
        alert("Error creating reservation: " + err.message);
    }
});

// ==================== Notifications ====================
const bell = document.getElementById("notification-bell");
const dropdown = document.getElementById("notification-dropdown");
const badge = document.getElementById("notification-badge");
const notifList = document.getElementById("notification-list");

bell.querySelector(".bell-icon").addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropdown.classList.toggle("active");
});

document.addEventListener("click", (e) => {
    if (!bell.contains(e.target)) dropdown.classList.remove("active");
});

document.getElementById("mark-all-read-btn").addEventListener("click", async () => {
    await markAllNotificationsRead(userId);
    loadNotifications();
});

async function loadNotifications() {
    try {
        await checkReminders(userId);
        const result = await getNotifications(userId);
        if (result.status === "success") {
            const notifications = result.notifications;
            const unreadCount = notifications.filter(n => !n.read).length;

            if (unreadCount > 0) {
                badge.textContent = unreadCount > 9 ? "9+" : unreadCount;
                badge.classList.remove("hidden");
            } else {
                badge.classList.add("hidden");
            }

            if (notifications.length === 0) {
                notifList.innerHTML = `<div class="notification-empty">No notifications</div>`;
                return;
            }

            notifList.innerHTML = notifications.slice(0, 20).map(n => {
                const timeAgo = getTimeAgo(n.createdAt);
                return `<div class="notification-item ${n.read ? "" : "unread"}" data-id="${n.notificationId}">
                    <div class="notification-item-title">${n.title}</div>
                    <div class="notification-item-message">${n.message}</div>
                    <div class="notification-item-time">${timeAgo}</div>
                </div>`;
            }).join("");

            notifList.querySelectorAll(".notification-item.unread").forEach(item => {
                item.addEventListener("click", async () => {
                    await markNotificationRead(parseInt(item.dataset.id));
                    item.classList.remove("unread");
                    const currentCount = parseInt(badge.textContent) || 0;
                    if (currentCount <= 1) badge.classList.add("hidden");
                    else badge.textContent = currentCount - 1;
                });
            });
        }
    } catch (err) {
        console.error("Error loading notifications:", err);
    }
}

function getTimeAgo(isoString) {
    const diff = Date.now() - new Date(isoString).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "Just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
}

// ==================== Init ====================
loadReservations();
loadNotifications();
setInterval(loadNotifications, 60000);
