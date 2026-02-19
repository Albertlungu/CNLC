/**
 * Shared Navbar Component
 *
 * Renders the same nav bar that was previously inlined in each page.
 * Items: Agent, Directory, Map, Trending, Deals, Saved, Friends,
 *        Reservations, Calendar, Blogs, Profile, Logout
 *
 * Usage: import { initNavbar } from "./components/navbar.js";
 *        initNavbar("directory");
 */

import { logout } from "../api-client.js";

const NAV_ITEMS = [
    { key: "agent", label: "Agent", emoji: "\uD83E\uDD16", href: "agent.html" },
    { key: "directory", label: "Directory", emoji: "\uD83C\uDFE0", href: "businesses.html" },
    { key: "map", label: "Map", emoji: "\uD83D\uDCCD", href: "map.html" },
    { key: "trending", label: "Trending", emoji: "\uD83D\uDD25", href: "trending.html" },
    { key: "deals", label: "Deals", emoji: "\uD83D\uDCB0", href: "deals.html" },
    { key: "saved", label: "Saved", emoji: "\u2B50", href: "saved.html" },
    { key: "friends", label: "Friends", emoji: "\uD83D\uDC65", href: "friends.html" },
    { key: "reservations", label: "Reservations", emoji: "\uD83D\uDCC5", href: "reservations.html" },
    { key: "calendar", label: "Calendar", emoji: "\uD83D\uDDD3\uFE0F", href: "calendar.html" },
    { key: "blogs", label: "Blogs", emoji: "\uD83D\uDCDD", href: "blogs.html" },
    { key: "profile", label: "Profile", emoji: "\uD83D\uDC64", href: "profile.html" },
];

/**
 * Initialize the navbar. Replaces any existing <nav class="menu-bar">.
 * @param {string} activePage - key of the current page
 */
export function initNavbar(activePage) {
    const nav = document.createElement("nav");
    nav.className = "menu-bar";

    let html = '<ul class="menu-links">';

    for (const item of NAV_ITEMS) {
        const activeClass = item.key === activePage ? ' class="active"' : "";
        html += `<li><a href="${item.href}"${activeClass}><span class="menu-emoji">${item.emoji}</span><span class="menu-text">${item.label}</span></a></li>`;
    }

    // Logout
    html += '<li><a href="#" id="logout-btn" class="logout-link"><span class="menu-emoji">\uD83D\uDEAA</span><span class="menu-text">Logout</span></a></li>';
    html += "</ul>";

    nav.innerHTML = html;

    // Replace existing nav
    const existing = document.querySelector("nav.menu-bar");
    if (existing) {
        existing.replaceWith(nav);
    } else {
        document.body.prepend(nav);
    }

    // Logout handler
    const logoutBtn = nav.querySelector("#logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", (e) => {
            e.preventDefault();
            logout();
        });
    }
}

