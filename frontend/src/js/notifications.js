/**
 * Notification bell component - can be imported on any page.
 * Injects notification bell HTML into the nav and handles fetching/display.
 */
import { getSession, getNotifications, markNotificationRead, markAllNotificationsRead, checkReminders } from "./api-client.js";

export function initNotifications() {
    const session = getSession();
    if (!session) return;
    const userId = session.userId;

    // Inject bell into nav
    const menuLinks = document.querySelector(".menu-links");
    if (!menuLinks) return;

    // Check if already injected
    if (document.getElementById("notification-bell")) return;

    const logoutLi = menuLinks.querySelector("li:last-child");
    const bellLi = document.createElement("li");
    bellLi.className = "notification-bell";
    bellLi.id = "notification-bell";
    bellLi.innerHTML = `
        <a href="#" class="bell-icon">Notifications</a>
        <span class="notification-badge hidden" id="notification-badge">0</span>
        <div class="notification-dropdown" id="notification-dropdown">
            <div class="notification-dropdown-header">
                <h3>Notifications</h3>
                <button class="mark-all-read-btn" id="mark-all-read-btn">Mark all read</button>
            </div>
            <div class="notification-list" id="notification-list">
                <div class="notification-empty">No notifications</div>
            </div>
        </div>
    `;

    menuLinks.insertBefore(bellLi, logoutLi);

    // Load notification CSS if not already loaded
    if (!document.querySelector('link[href="css/notifications.css"]')) {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = "css/notifications.css";
        document.head.appendChild(link);
    }

    // Event handlers
    const bell = bellLi;
    const dropdown = bell.querySelector("#notification-dropdown");
    const badge = bell.querySelector("#notification-badge");
    const notifList = bell.querySelector("#notification-list");

    bell.querySelector(".bell-icon").addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropdown.classList.toggle("active");
    });

    document.addEventListener("click", (e) => {
        if (!bell.contains(e.target)) dropdown.classList.remove("active");
    });

    bell.querySelector("#mark-all-read-btn").addEventListener("click", async () => {
        await markAllNotificationsRead(userId);
        loadNotifs();
    });

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

    async function loadNotifs() {
        try {
            await checkReminders(userId);
            const result = await getNotifications(userId);
            if (result.status !== "success") return;

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

            notifList.innerHTML = notifications.slice(0, 20).map(n => `
                <div class="notification-item ${n.read ? "" : "unread"}" data-id="${n.notificationId}">
                    <div class="notification-item-title">${n.title}</div>
                    <div class="notification-item-message">${n.message}</div>
                    <div class="notification-item-time">${getTimeAgo(n.createdAt)}</div>
                </div>
            `).join("");

            notifList.querySelectorAll(".notification-item.unread").forEach(item => {
                item.addEventListener("click", async () => {
                    await markNotificationRead(parseInt(item.dataset.id));
                    item.classList.remove("unread");
                    const count = parseInt(badge.textContent) || 0;
                    if (count <= 1) badge.classList.add("hidden");
                    else badge.textContent = count - 1;
                });
            });
        } catch (err) {
            console.error("Notification load error:", err);
        }
    }

    loadNotifs();
    setInterval(loadNotifs, 60000);
}
