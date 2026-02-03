/**
 * Mobile hamburger menu toggle.
 * Dynamically adds a hamburger button and toggles the nav on mobile viewports.
 */
export function initMobileNav() {
    const menuBar = document.querySelector(".menu-bar");
    if (!menuBar) return;

    const menuLinks = menuBar.querySelector(".menu-links");
    if (!menuLinks) return;

    // Create hamburger button
    const hamburger = document.createElement("button");
    hamburger.className = "hamburger-btn";
    hamburger.setAttribute("aria-label", "Toggle navigation menu");
    hamburger.innerHTML = `<span></span><span></span><span></span>`;
    menuBar.insertBefore(hamburger, menuLinks);

    hamburger.addEventListener("click", () => {
        menuLinks.classList.toggle("mobile-open");
        hamburger.classList.toggle("active");
    });

    // Close menu when clicking a link
    menuLinks.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => {
            menuLinks.classList.remove("mobile-open");
            hamburger.classList.remove("active");
        });
    });
}
