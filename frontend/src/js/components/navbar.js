/**
 * Shared Navbar Component
 *
 * Renders a grouped nav bar with dropdown categories:
 *   - Agent (standalone)
 *   - Explore: Directory, Map, Trending
 *   - Activity: Deals, Saved, Reservations, Calendar
 *   - Social: Friends, Blogs
 *   - Profile (standalone)
 *   - Logout
 *
 * Usage: import { initNavbar } from "./components/navbar.js";
 *        initNavbar("directory");
 */

import { logout } from "../api-client.js";

const NAV_GROUPS = [
    { key: "agent", label: "Agent", emoji: "\uD83E\uDD16", href: "agent.html" },
    {
        key: "explore",
        label: "Explore",
        emoji: "\uD83D\uDD0D",
        children: [
            { key: "directory", label: "Directory", emoji: "\uD83C\uDFE0", href: "businesses.html" },
            { key: "map", label: "Map", emoji: "\uD83D\uDCCD", href: "map.html" },
            { key: "trending", label: "Trending", emoji: "\uD83D\uDD25", href: "trending.html" },
        ],
    },
    {
        key: "activity",
        label: "Activity",
        emoji: "\uD83D\uDCCB",
        children: [
            { key: "deals", label: "Deals", emoji: "\uD83D\uDCB0", href: "deals.html" },
            { key: "saved", label: "Saved", emoji: "\u2B50", href: "saved.html" },
            { key: "reservations", label: "Reservations", emoji: "\uD83D\uDCC5", href: "reservations.html" },
            { key: "calendar", label: "Calendar", emoji: "\uD83D\uDDD3\uFE0F", href: "calendar.html" },
        ],
    },
    {
        key: "social",
        label: "Social",
        emoji: "\uD83D\uDCAC",
        children: [
            { key: "friends", label: "Friends", emoji: "\uD83D\uDC65", href: "friends.html" },
            { key: "blogs", label: "Blogs", emoji: "\uD83D\uDCDD", href: "blogs.html" },
        ],
    },
    { key: "profile", label: "Profile", emoji: "\uD83D\uDC64", href: "profile.html" },
];

/**
 * Check whether the active page belongs to a group's children.
 */
function groupContainsActive(group, activePage) {
    if (!group.children) return false;
    return group.children.some((c) => c.key === activePage);
}

/**
 * Initialize the navbar. Replaces any existing <nav class="menu-bar">.
 * @param {string} activePage - key of the current page
 */
export function initNavbar(activePage) {
    const nav = document.createElement("nav");
    nav.className = "menu-bar";

    let html = '<ul class="menu-links">';

    for (const group of NAV_GROUPS) {
        if (group.children) {
            // Dropdown group
            const isGroupActive = groupContainsActive(group, activePage);
            const groupActiveClass = isGroupActive ? " group-active" : "";
            html += `<li class="nav-group${groupActiveClass}">`;
            html += `<button class="nav-group-toggle" aria-expanded="false"><span class="menu-emoji">${group.emoji}</span><span class="menu-text">${group.label}</span><span class="dropdown-arrow">&#9662;</span></button>`;
            html += '<ul class="nav-dropdown">';
            for (const child of group.children) {
                const activeClass = child.key === activePage ? ' class="active"' : "";
                html += `<li><a href="${child.href}"${activeClass}><span class="menu-emoji">${child.emoji}</span><span class="menu-text">${child.label}</span></a></li>`;
            }
            html += "</ul>";
            html += "</li>";
        } else {
            // Standalone item
            const activeClass = group.key === activePage ? ' class="active"' : "";
            html += `<li><a href="${group.href}"${activeClass}><span class="menu-emoji">${group.emoji}</span><span class="menu-text">${group.label}</span></a></li>`;
        }
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

    // Dropdown toggle handlers
    nav.querySelectorAll(".nav-group-toggle").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            const li = btn.closest(".nav-group");
            const wasOpen = li.classList.contains("open");

            // Close all dropdowns first
            nav.querySelectorAll(".nav-group").forEach((g) => {
                g.classList.remove("open");
                g.querySelector(".nav-group-toggle")?.setAttribute("aria-expanded", "false");
            });

            if (!wasOpen) {
                li.classList.add("open");
                btn.setAttribute("aria-expanded", "true");
            }
        });
    });

    // Close dropdowns when clicking outside
    document.addEventListener("click", (e) => {
        if (!nav.contains(e.target)) {
            nav.querySelectorAll(".nav-group").forEach((g) => {
                g.classList.remove("open");
                g.querySelector(".nav-group-toggle")?.setAttribute("aria-expanded", "false");
            });
        }
    });

    // Initialize mobile hamburger nav
    _initMobileNav(nav);
}

/**
 * Mobile hamburger menu -- integrated into initNavbar so every page gets it
 * automatically without needing a separate import.
 */
function _initMobileNav(nav) {
    const menuLinks = nav.querySelector(".menu-links");
    if (!menuLinks) return;

    const hamburger = document.createElement("button");
    hamburger.className = "hamburger-btn";
    hamburger.setAttribute("aria-label", "Toggle navigation menu");
    hamburger.innerHTML = "<span></span><span></span><span></span>";
    nav.insertBefore(hamburger, menuLinks);

    hamburger.addEventListener("click", () => {
        menuLinks.classList.toggle("mobile-open");
        hamburger.classList.toggle("active");
    });

    // Close menu when clicking a direct link (not a dropdown toggle)
    menuLinks.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => {
            menuLinks.classList.remove("mobile-open");
            hamburger.classList.remove("active");
        });
    });
}

