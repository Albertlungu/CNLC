/**
 * Shared Navbar Component
 *
 * Primary links: Directory (+ Map sub-link), Deals, Calendar, Profile (+ Logout)
 * Explore dropdown: Trending, Saved, Friends, Reservations, Agent, Blogs
 *
 * Usage: import { initNavbar } from "./components/navbar.js";
 *        initNavbar("directory"); // pass the active page key
 */

import { logout } from "../api-client.js";

const NAV_ITEMS = {
    primary: [
        { key: "directory", label: "Directory", emoji: "\uD83C\uDFE0", href: "businesses.html", sub: { key: "map", label: "Map", emoji: "\uD83D\uDCCD", href: "map.html" } },
        { key: "deals", label: "Deals", emoji: "\uD83D\uDCB0", href: "deals.html" },
        { key: "calendar", label: "Calendar", emoji: "\uD83D\uDCC5", href: "calendar.html" },
        { key: "profile", label: "Profile", emoji: "\uD83D\uDC64", href: "profile.html" },
    ],
    explore: [
        { key: "trending", label: "Trending", emoji: "\uD83D\uDD25", href: "trending.html" },
        { key: "saved", label: "Saved", emoji: "\u2B50", href: "saved.html" },
        { key: "friends", label: "Friends", emoji: "\uD83D\uDC65", href: "friends.html" },
        { key: "reservations", label: "Reservations", emoji: "\uD83D\uDCC5", href: "reservations.html" },
        { key: "agent", label: "Agent", emoji: "\uD83E\uDD16", href: "agent.html" },
        { key: "blogs", label: "Blogs", emoji: "\uD83D\uDCDD", href: "blogs.html" },
    ],
};

/**
 * Initialize the navbar. Replaces any existing <nav class="menu-bar"> or
 * injects at the start of <body>.
 *
 * @param {string} activePage - key of the currently active page (e.g. "directory", "deals", "profile")
 */
export function initNavbar(activePage) {
    const nav = document.createElement("nav");
    nav.className = "menu-bar";
    nav.innerHTML = buildNavHTML(activePage);

    // Replace existing nav if present, otherwise prepend to body
    const existing = document.querySelector("nav.menu-bar");
    if (existing) {
        existing.replaceWith(nav);
    } else {
        document.body.prepend(nav);
    }

    // Wire up interactions
    setupExploreDropdown(nav);
    setupLogout(nav);
}

function buildNavHTML(activePage) {
    let html = '<ul class="menu-links">';

    // Primary items
    for (const item of NAV_ITEMS.primary) {
        const isActive = item.key === activePage || (item.sub && item.sub.key === activePage);
        const activeClass = isActive ? ' class="active"' : "";

        if (item.sub) {
            // Directory has a Map sub-link
            const subActive = item.sub.key === activePage ? ' class="active"' : "";
            html += `<li class="has-sub">`;
            html += `<a href="${item.href}"${activeClass}><span class="menu-emoji">${item.emoji}</span><span class="menu-text">${item.label}</span></a>`;
            html += `<a href="${item.sub.href}" class="sub-link${item.sub.key === activePage ? " active" : ""}"><span class="menu-emoji">${item.sub.emoji}</span><span class="menu-text">${item.sub.label}</span></a>`;
            html += `</li>`;
        } else {
            html += `<li><a href="${item.href}"${activeClass}><span class="menu-emoji">${item.emoji}</span><span class="menu-text">${item.label}</span></a></li>`;
        }
    }

    // Explore dropdown
    const exploreActive = NAV_ITEMS.explore.some(i => i.key === activePage);
    html += `<li class="explore-dropdown${exploreActive ? " explore-active" : ""}">`;
    html += `<button class="explore-toggle" aria-expanded="false" aria-haspopup="true">`;
    html += `<span class="menu-emoji">\u2630</span><span class="menu-text">Explore</span>`;
    html += `<span class="explore-arrow"></span>`;
    html += `</button>`;
    html += `<ul class="explore-menu">`;
    for (const item of NAV_ITEMS.explore) {
        const activeClass = item.key === activePage ? ' class="active"' : "";
        html += `<li><a href="${item.href}"${activeClass}><span class="menu-emoji">${item.emoji}</span><span class="menu-text">${item.label}</span></a></li>`;
    }
    html += `</ul>`;
    html += `</li>`;

    // Logout
    html += `<li><a href="#" id="logout-btn" class="logout-link"><span class="menu-emoji">\uD83D\uDEAA</span><span class="menu-text">Logout</span></a></li>`;

    html += "</ul>";
    return html;
}

function setupExploreDropdown(nav) {
    const toggle = nav.querySelector(".explore-toggle");
    const dropdown = nav.querySelector(".explore-dropdown");
    if (!toggle || !dropdown) return;

    toggle.addEventListener("click", (e) => {
        e.stopPropagation();
        const isOpen = dropdown.classList.toggle("open");
        toggle.setAttribute("aria-expanded", isOpen);
    });

    // Close on outside click
    document.addEventListener("click", (e) => {
        if (!dropdown.contains(e.target)) {
            dropdown.classList.remove("open");
            toggle.setAttribute("aria-expanded", "false");
        }
    });

    // Close on Escape
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            dropdown.classList.remove("open");
            toggle.setAttribute("aria-expanded", "false");
        }
    });
}

function setupLogout(nav) {
    const logoutBtn = nav.querySelector("#logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", (e) => {
            e.preventDefault();
            logout();
        });
    }
}
