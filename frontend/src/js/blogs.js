import { requireAuth, getSession, getBlogFeed } from "./api-client.js";
import { initNavbar } from "./components/navbar.js";

if (!requireAuth()) {
    throw new Error("Authentication required");
}
initNavbar("blogs");

const feedContainer = document.getElementById("blog-feed");
const loadMoreContainer = document.getElementById("load-more-container");
const loadMoreBtn = document.getElementById("load-more-btn");
const tagInput = document.getElementById("tag-input");
const filterBtn = document.getElementById("filter-btn");
const clearFilterBtn = document.getElementById("clear-filter-btn");

let currentOffset = 0;
const PAGE_SIZE = 20;
let activeTag = null;

async function loadFeed(append = false) {
    if (!append) {
        feedContainer.innerHTML = '<div class="loading">Loading blog posts...</div>';
        currentOffset = 0;
    }

    try {
        const result = await getBlogFeed(PAGE_SIZE, currentOffset, activeTag);
        const posts = result.posts || [];

        if (!append) {
            feedContainer.innerHTML = "";
        }

        if (posts.length === 0 && currentOffset === 0) {
            feedContainer.innerHTML = '<p class="feed-empty">No blog posts yet. Check back later.</p>';
            loadMoreContainer.style.display = "none";
            return;
        }

        for (const post of posts) {
            const el = document.createElement("article");
            el.className = "feed-post";

            const date = new Date(post.createdAt).toLocaleDateString("en-CA", {
                year: "numeric", month: "long", day: "numeric"
            });

            let coverHtml = "";
            if (post.coverImage) {
                coverHtml = `<img src="${post.coverImage}" alt="" class="feed-cover">`;
            }

            let tagsHtml = "";
            if (post.tags && post.tags.length) {
                tagsHtml = `<div class="feed-tags">${post.tags.map(t => `<span class="feed-tag" data-tag="${t}">${t}</span>`).join("")}</div>`;
            }

            // Simple markdown rendering
            let contentHtml = post.content
                .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
                .replace(/^### (.+)$/gm, "<h4>$1</h4>")
                .replace(/^## (.+)$/gm, "<h3>$1</h3>")
                .replace(/^# (.+)$/gm, "<h2>$1</h2>")
                .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
                .replace(/\*(.+?)\*/g, "<em>$1</em>")
                .replace(/\n/g, "<br>");

            // Truncate for feed
            const maxLen = 300;
            let truncated = false;
            if (contentHtml.length > maxLen) {
                contentHtml = contentHtml.substring(0, maxLen) + "...";
                truncated = true;
            }

            const businessLink = post.businessId
                ? `<a href="business-detail.html?id=${post.businessId}" class="feed-business-link">${post.businessName || "View Business"}</a>`
                : "";

            el.innerHTML = `
                ${coverHtml}
                <div class="feed-post-body">
                    <div class="feed-post-meta">
                        <span class="feed-date">${date}</span>
                        ${businessLink}
                    </div>
                    <h2 class="feed-post-title">${post.title}</h2>
                    ${tagsHtml}
                    <div class="feed-post-content">${contentHtml}</div>
                    ${truncated ? `<a href="business-detail.html?id=${post.businessId}" class="read-more">Read more</a>` : ""}
                </div>
            `;

            feedContainer.appendChild(el);
        }

        // Wire tag clicks
        feedContainer.querySelectorAll(".feed-tag").forEach(tagEl => {
            tagEl.addEventListener("click", () => {
                activeTag = tagEl.dataset.tag;
                tagInput.value = activeTag;
                clearFilterBtn.style.display = "inline-flex";
                loadFeed(false);
            });
        });

        currentOffset += posts.length;
        loadMoreContainer.style.display = posts.length >= PAGE_SIZE ? "block" : "none";
    } catch (err) {
        console.error("Error loading blog feed:", err);
        if (!append) {
            feedContainer.innerHTML = '<p class="feed-error">Failed to load blog posts.</p>';
        }
    }
}

filterBtn.addEventListener("click", () => {
    const tag = tagInput.value.trim();
    activeTag = tag || null;
    clearFilterBtn.style.display = tag ? "inline-flex" : "none";
    loadFeed(false);
});

clearFilterBtn.addEventListener("click", () => {
    activeTag = null;
    tagInput.value = "";
    clearFilterBtn.style.display = "none";
    loadFeed(false);
});

tagInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        e.preventDefault();
        filterBtn.click();
    }
});

loadMoreBtn.addEventListener("click", () => {
    loadFeed(true);
});

loadFeed(false);
