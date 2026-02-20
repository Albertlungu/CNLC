/**
 * calendar.js - Google Calendar integration via server-side OAuth.
 * All Google Calendar API calls are proxied through the backend.
 */
import {
    requireAuth, getSession, logout,
    getCalendarAuthUrl, getCalendarEvents, createCalendarEvent,
    updateCalendarEvent, deleteCalendarEvent, getCalendarStatus, disconnectCalendar,
} from "./api-client.js";
import { initNavbar } from "./components/navbar.js";

if (!requireAuth()) throw new Error("Not authenticated");
initNavbar("calendar");

const session = getSession();
const userId = session.userId;

// ==================== State ====================
let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth();
let selectedDate = new Date();
let allEvents = [];
let isGoogleConnected = false;

// ==================== DOM ====================
const monthLabel = document.getElementById("current-month-label");
const daysContainer = document.getElementById("calendar-days");
const eventsDateLabel = document.getElementById("events-date-label");
const eventsList = document.getElementById("events-list");
const connectBtn = document.getElementById("connect-google-btn");
const addEventBtn = document.getElementById("add-event-btn");
const googleStatus = document.getElementById("google-status");
const googleEmail = document.getElementById("google-email");
const disconnectBtn = document.getElementById("disconnect-google");
const addEventModal = document.getElementById("add-event-modal");
const eventModalClose = document.getElementById("event-modal-close");
const eventCancel = document.getElementById("event-cancel");
const eventSubmit = document.getElementById("event-submit");

// ==================== Google Calendar Connection ====================
async function checkConnection() {
    try {
        const result = await getCalendarStatus(userId);
        if (result.connected) {
            isGoogleConnected = true;
            connectBtn.style.display = "none";
            addEventBtn.style.display = "inline-flex";
            googleStatus.style.display = "flex";
            googleEmail.textContent = `Connected: ${result.email || "Google Calendar"}`;
        } else {
            isGoogleConnected = false;
            connectBtn.style.display = "inline-flex";
            addEventBtn.style.display = "none";
            googleStatus.style.display = "none";
        }
    } catch {
        isGoogleConnected = false;
    }
}

connectBtn.addEventListener("click", async () => {
    try {
        const result = await getCalendarAuthUrl(userId);
        if (result.status === "success" && result.authUrl) {
            window.location.href = result.authUrl;
        } else {
            alert(result.message || "Failed to start Google Calendar connection.");
        }
    } catch (err) {
        alert("Error connecting to Google Calendar: " + err.message);
    }
});

disconnectBtn.addEventListener("click", async () => {
    if (!confirm("Disconnect Google Calendar?")) return;
    try {
        await disconnectCalendar(userId);
        isGoogleConnected = false;
        connectBtn.style.display = "inline-flex";
        addEventBtn.style.display = "none";
        googleStatus.style.display = "none";
        await fetchEvents();
        renderCalendar();
        showDayEvents(selectedDate);
    } catch (err) {
        alert("Error disconnecting: " + err.message);
    }
});

// ==================== Fetch Events (Merged) ====================
async function fetchEvents() {
    const month = `${currentYear}-${String(currentMonth + 1).padStart(2, "0")}`;
    try {
        const result = await getCalendarEvents(userId, month);
        if (result.status === "success") {
            allEvents = result.events || [];
        } else {
            allEvents = [];
        }
    } catch {
        allEvents = [];
    }
}

// ==================== Calendar Rendering ====================
const MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
];

function renderCalendar() {
    monthLabel.textContent = `${MONTH_NAMES[currentMonth]} ${currentYear}`;

    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const daysInPrevMonth = new Date(currentYear, currentMonth, 0).getDate();

    const today = new Date();
    daysContainer.innerHTML = "";

    // Previous month filler days
    for (let i = firstDay - 1; i >= 0; i--) {
        const dayNum = daysInPrevMonth - i;
        const cell = createDayCell(dayNum, true, currentYear, currentMonth - 1);
        daysContainer.appendChild(cell);
    }

    // Current month days
    for (let d = 1; d <= daysInMonth; d++) {
        const isToday = d === today.getDate() && currentMonth === today.getMonth() && currentYear === today.getFullYear();
        const isSelected = d === selectedDate.getDate() && currentMonth === selectedDate.getMonth() && currentYear === selectedDate.getFullYear();
        const cell = createDayCell(d, false, currentYear, currentMonth, isToday, isSelected);
        daysContainer.appendChild(cell);
    }

    // Next month filler days
    const totalCells = daysContainer.children.length;
    const remaining = (7 - (totalCells % 7)) % 7;
    for (let d = 1; d <= remaining; d++) {
        const cell = createDayCell(d, true, currentYear, currentMonth + 1);
        daysContainer.appendChild(cell);
    }
}

function createDayCell(dayNum, otherMonth, year, month, isToday = false, isSelected = false) {
    const cell = document.createElement("div");
    cell.className = "calendar-day";
    if (otherMonth) cell.classList.add("other-month");
    if (isToday) cell.classList.add("today");
    if (isSelected) cell.classList.add("selected");

    const num = document.createElement("div");
    num.className = "day-number";
    num.textContent = dayNum;
    cell.appendChild(num);

    // Normalize month for date string
    const actualMonth = ((month % 12) + 12) % 12;
    let actualYear = year;
    if (month < 0) actualYear--;
    if (month > 11) actualYear++;
    const dateStr = `${actualYear}-${String(actualMonth + 1).padStart(2, "0")}-${String(dayNum).padStart(2, "0")}`;

    const dayEvents = allEvents.filter(e => {
        const eDate = (e.start || "").substring(0, 10);
        return eDate === dateStr;
    });

    // Show up to 3 event chips
    dayEvents.slice(0, 3).forEach(e => {
        const chip = document.createElement("div");
        chip.className = `day-event ${e.source}`;
        chip.textContent = e.title;
        cell.appendChild(chip);
    });

    if (dayEvents.length > 3) {
        const more = document.createElement("div");
        more.className = "day-event";
        more.textContent = `+${dayEvents.length - 3} more`;
        more.style.color = "var(--text-muted, #888)";
        more.style.fontSize = "9px";
        cell.appendChild(more);
    }

    if (!otherMonth) {
        cell.addEventListener("click", () => {
            document.querySelectorAll(".calendar-day.selected").forEach(c => c.classList.remove("selected"));
            cell.classList.add("selected");
            selectedDate = new Date(year, month, dayNum);
            showDayEvents(selectedDate);
        });
    }

    return cell;
}

function showDayEvents(date) {
    const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
    const today = new Date();
    const isToday = date.getDate() === today.getDate() && date.getMonth() === today.getMonth() && date.getFullYear() === today.getFullYear();

    eventsDateLabel.textContent = isToday
        ? "Today's Events"
        : `Events for ${MONTH_NAMES[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`;

    const dayEvents = allEvents.filter(e => (e.start || "").substring(0, 10) === dateStr);

    if (dayEvents.length === 0) {
        eventsList.innerHTML = `<p class="events-empty">No events for this day</p>`;
        return;
    }

    // Sort by time
    dayEvents.sort((a, b) => (a.start || "").localeCompare(b.start || ""));

    eventsList.innerHTML = dayEvents.map(e => {
        const time = e.allDay ? "All day" : formatTime(e.start);
        const sourceLabel = e.source === "google" ? "Google Calendar" : "Discovereye Reservation";
        const sourceClass = e.source;

        let actions = "";
        if (e.source === "google" && isGoogleConnected) {
            actions = `
                <div class="event-actions">
                    <button class="event-edit-btn" data-event-id="${e.id}" data-title="${escapeAttr(e.title)}" data-start="${e.start}" data-end="${e.end || ''}" data-desc="${escapeAttr(e.description || '')}">Edit</button>
                    <button class="event-delete-btn" data-event-id="${e.id}">Delete</button>
                </div>
            `;
        } else if (e.source === "discovereye" && isGoogleConnected) {
            actions = `<button class="event-add-to-gcal" data-title="${escapeAttr(e.title)}" data-start="${e.start}">Add to GCal</button>`;
        }

        return `
            <div class="event-card">
                <div class="event-time">${time}</div>
                <div class="event-details">
                    <div class="event-title">${escapeHtml(e.title)}</div>
                    <div class="event-source ${sourceClass}">${sourceLabel}</div>
                    ${e.description ? `<div class="event-description">${escapeHtml(e.description)}</div>` : ""}
                </div>
                ${actions}
            </div>
        `;
    }).join("");

    // Bind action buttons
    eventsList.querySelectorAll(".event-delete-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
            if (!confirm("Delete this event from Google Calendar?")) return;
            btn.textContent = "Deleting...";
            btn.disabled = true;
            try {
                await deleteCalendarEvent(userId, btn.dataset.eventId);
                await fetchEvents();
                renderCalendar();
                showDayEvents(selectedDate);
            } catch {
                btn.textContent = "Failed";
            }
        });
    });

    eventsList.querySelectorAll(".event-edit-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            // Populate modal with existing event data
            const start = btn.dataset.start || "";
            const end = btn.dataset.end || "";
            document.getElementById("event-title").value = btn.dataset.title || "";
            document.getElementById("event-date").value = start.substring(0, 10);
            document.getElementById("event-start-time").value = start.substring(11, 16) || "12:00";
            document.getElementById("event-end-time").value = end.substring(11, 16) || "13:00";
            document.getElementById("event-description").value = btn.dataset.desc || "";
            addEventModal.dataset.editEventId = btn.dataset.eventId;
            addEventModal.style.display = "flex";
        });
    });

    eventsList.querySelectorAll(".event-add-to-gcal").forEach(btn => {
        btn.addEventListener("click", async () => {
            const title = btn.dataset.title;
            const start = btn.dataset.start;
            const date = start.substring(0, 10);
            const time = start.substring(11, 16) || "12:00";
            const endH = parseInt(time.split(":")[0]) + 1;
            const endTime = `${String(endH).padStart(2, "0")}:${time.split(":")[1]}`;

            btn.textContent = "Adding...";
            btn.disabled = true;
            try {
                const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
                await createCalendarEvent(userId, title, date, time, endTime, "Added from Discovereye", tz);
                btn.textContent = "Added";
                await fetchEvents();
                renderCalendar();
            } catch {
                btn.textContent = "Failed";
            }
        });
    });
}

function formatTime(dateTimeStr) {
    if (!dateTimeStr) return "";
    const d = new Date(dateTimeStr);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function escapeAttr(str) {
    return (str || "").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

// ==================== Navigation ====================
document.getElementById("prev-month").addEventListener("click", async () => {
    currentMonth--;
    if (currentMonth < 0) { currentMonth = 11; currentYear--; }
    await fetchEvents();
    renderCalendar();
});

document.getElementById("next-month").addEventListener("click", async () => {
    currentMonth++;
    if (currentMonth > 11) { currentMonth = 0; currentYear++; }
    await fetchEvents();
    renderCalendar();
});

// ==================== Add/Edit Event Modal ====================
addEventBtn.addEventListener("click", () => {
    document.getElementById("event-title").value = "";
    document.getElementById("event-description").value = "";
    document.getElementById("event-date").value = `${selectedDate.getFullYear()}-${String(selectedDate.getMonth() + 1).padStart(2, "0")}-${String(selectedDate.getDate()).padStart(2, "0")}`;
    document.getElementById("event-start-time").value = "12:00";
    document.getElementById("event-end-time").value = "13:00";
    delete addEventModal.dataset.editEventId;
    addEventModal.style.display = "flex";
});

eventModalClose.addEventListener("click", () => { addEventModal.style.display = "none"; });
eventCancel.addEventListener("click", () => { addEventModal.style.display = "none"; });
addEventModal.addEventListener("click", (e) => {
    if (e.target === addEventModal) addEventModal.style.display = "none";
});

eventSubmit.addEventListener("click", async () => {
    const title = document.getElementById("event-title").value.trim();
    const date = document.getElementById("event-date").value;
    const startTime = document.getElementById("event-start-time").value;
    const endTime = document.getElementById("event-end-time").value;
    const description = document.getElementById("event-description").value.trim();
    const editEventId = addEventModal.dataset.editEventId;

    if (!title || !date || !startTime || !endTime) {
        alert("Please fill in title, date, and times.");
        return;
    }

    eventSubmit.textContent = editEventId ? "Updating..." : "Adding...";
    eventSubmit.disabled = true;

    try {
        const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
        if (editEventId) {
            await updateCalendarEvent(userId, editEventId, { title, date, startTime, endTime, description, timezone: tz });
        } else {
            await createCalendarEvent(userId, title, date, startTime, endTime, description, tz);
        }
        addEventModal.style.display = "none";
        await fetchEvents();
        renderCalendar();
        showDayEvents(selectedDate);
    } catch {
        alert("Failed to save event. Please try again.");
    }

    eventSubmit.textContent = "Add Event";
    eventSubmit.disabled = false;
});

// ==================== Init ====================
async function init() {
    // Check URL params for connection status
    const params = new URLSearchParams(window.location.search);
    if (params.get("connected") === "true") {
        // Clean URL
        window.history.replaceState({}, "", "calendar.html");
    }
    if (params.get("error")) {
        alert("Google Calendar connection error: " + params.get("error"));
        window.history.replaceState({}, "", "calendar.html");
    }

    await checkConnection();
    await fetchEvents();
    renderCalendar();
    showDayEvents(selectedDate);
}

init();
