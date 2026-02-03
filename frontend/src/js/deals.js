import { requireAuth, logout, getSession, getDeals, createDeal, deleteDeal, scrapeDeals, filterBusinesses, getBusinessById } from "./api-client.js";
import { initNotifications } from "./notifications.js";

if (!requireAuth()) {
    throw new Error("Authentication required");
}
initNotifications();

const session = getSession();
const userId = session.userId;

const dealsGrid = document.getElementById("deals-grid");
const createDealBtn = document.getElementById("create-deal-btn");
const fetchDealsBtn = document.getElementById("fetch-deals-btn");
const logoutBtn = document.getElementById("logout-btn");

// Create Deal Modal
const createModal = document.getElementById("create-deal-modal");
const createClose = document.getElementById("create-close");
const createForm = document.getElementById("create-deal-form");
const businessSearchInput = document.getElementById("deal-business-search");
const businessSearchResults = document.getElementById("business-search-results");
const businessIdInput = document.getElementById("deal-business-id");

// Fetch Deals Modal
const fetchModal = document.getElementById("fetch-deals-modal");
const fetchClose = document.getElementById("fetch-close");
const fetchBusinessSearch = document.getElementById("fetch-business-search");
const fetchSearchResults = document.getElementById("fetch-search-results");
const fetchBusinessId = document.getElementById("fetch-business-id");
const fetchBusinessName = document.getElementById("fetch-business-name");
const fetchSubmitBtn = document.getElementById("fetch-submit-btn");
const fetchStatus = document.getElementById("fetch-status");
const fetchCity = document.getElementById("fetch-city");

let searchTimeout = null;

async function loadDeals() {
    dealsGrid.innerHTML = '<div class="loading">Loading deals...</div>';

    try {
        const result = await getDeals();
        if (result.status === "success") {
            if (result.deals.length === 0) {
                dealsGrid.innerHTML = '<div class="no-deals">No deals available yet. Create one or fetch from the web.</div>';
                return;
            }

            dealsGrid.innerHTML = "";
            for (const deal of result.deals) {
                const card = await createDealCard(deal);
                dealsGrid.appendChild(card);
            }
        }
    } catch (error) {
        console.error("Error loading deals:", error);
        dealsGrid.innerHTML = '<div class="no-deals">Failed to load deals.</div>';
    }
}

async function createDealCard(deal) {
    const card = document.createElement("div");
    card.className = "deal-card";

    // Get business name
    let businessName = `Business #${deal.businessId}`;
    try {
        const biz = await getBusinessById(deal.businessId);
        if (biz.status === "success" && biz.business) {
            businessName = biz.business.name;
        }
    } catch (e) { /* use default */ }

    const badgeText = formatDiscount(deal.discountType, deal.discountValue);
    const expiresText = deal.expiresAt ? `Expires: ${new Date(deal.expiresAt).toLocaleDateString()}` : "";

    card.innerHTML = `
        <div class="deal-business-name">${businessName}</div>
        <div class="deal-card-header">
            <span class="deal-title">${deal.title}</span>
            ${badgeText ? `<span class="deal-badge">${badgeText}</span>` : ""}
        </div>
        ${deal.description ? `<div class="deal-description">${deal.description}</div>` : ""}
        <div class="deal-meta">
            <span class="deal-source">${deal.source === "scraped" && deal.sourceUrl ? `<a href="${deal.sourceUrl}" target="_blank">Source</a>` : deal.source}</span>
            ${expiresText ? `<span class="deal-expires">${expiresText}</span>` : ""}
        </div>
        <div class="deal-actions">
            <button class="deal-delete-btn" data-deal-id="${deal.dealId}">Remove</button>
        </div>
    `;

    const deleteBtn = card.querySelector(".deal-delete-btn");
    deleteBtn.addEventListener("click", async () => {
        const result = await deleteDeal(deal.dealId);
        if (result.status === "success") {
            card.remove();
            if (dealsGrid.children.length === 0) {
                dealsGrid.innerHTML = '<div class="no-deals">No deals available yet.</div>';
            }
        }
    });

    return card;
}

function formatDiscount(type, value) {
    if (!value && type !== "bogo") return "";
    switch (type) {
        case "percentage": return `${value}% OFF`;
        case "fixed": return `$${value} OFF`;
        case "bogo": return "BOGO";
        default: return "";
    }
}

// Business search for modals
async function searchBusinesses(query, resultsContainer, onSelect) {
    if (query.length < 2) {
        resultsContainer.classList.remove("active");
        return;
    }

    try {
        const result = await filterBusinesses(query, null, null, null, null, null, 0, 8);
        if (result.status === "success" && result.businesses.length > 0) {
            resultsContainer.innerHTML = result.businesses.map(b =>
                `<div class="search-dropdown-item" data-id="${b.id || b.businessId}" data-name="${b.name}">${b.name}</div>`
            ).join("");
            resultsContainer.classList.add("active");

            resultsContainer.querySelectorAll(".search-dropdown-item").forEach(item => {
                item.addEventListener("click", () => {
                    onSelect(parseInt(item.dataset.id), item.dataset.name);
                    resultsContainer.classList.remove("active");
                });
            });
        } else {
            resultsContainer.classList.remove("active");
        }
    } catch (e) {
        resultsContainer.classList.remove("active");
    }
}

// Event Listeners
document.addEventListener("DOMContentLoaded", () => {
    loadDeals();

    if (logoutBtn) {
        logoutBtn.addEventListener("click", (e) => {
            e.preventDefault();
            logout();
        });
    }

    // Create Deal Modal
    createDealBtn.addEventListener("click", () => createModal.classList.add("active"));
    createClose.addEventListener("click", () => createModal.classList.remove("active"));
    createModal.addEventListener("click", (e) => { if (e.target === createModal) createModal.classList.remove("active"); });

    businessSearchInput.addEventListener("input", () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchBusinesses(businessSearchInput.value.trim(), businessSearchResults, (id, name) => {
                businessIdInput.value = id;
                businessSearchInput.value = name;
            });
        }, 300);
    });

    createForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const businessId = parseInt(businessIdInput.value);
        if (!businessId) {
            alert("Please select a business");
            return;
        }

        const title = document.getElementById("deal-title").value.trim();
        const description = document.getElementById("deal-description").value.trim();
        const discountType = document.getElementById("deal-type").value;
        const discountValue = parseFloat(document.getElementById("deal-value").value) || null;
        const expiresAt = document.getElementById("deal-expires").value || null;

        const result = await createDeal(businessId, title, description, discountType, discountValue, expiresAt, userId);
        if (result.status === "success") {
            createModal.classList.remove("active");
            createForm.reset();
            businessIdInput.value = "";
            loadDeals();
        } else {
            alert("Failed to create deal: " + result.message);
        }
    });

    // Fetch Deals Modal
    fetchDealsBtn.addEventListener("click", () => fetchModal.classList.add("active"));
    fetchClose.addEventListener("click", () => fetchModal.classList.remove("active"));
    fetchModal.addEventListener("click", (e) => { if (e.target === fetchModal) fetchModal.classList.remove("active"); });

    fetchBusinessSearch.addEventListener("input", () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchBusinesses(fetchBusinessSearch.value.trim(), fetchSearchResults, (id, name) => {
                fetchBusinessId.value = id;
                fetchBusinessName.value = name;
                fetchBusinessSearch.value = name;
            });
        }, 300);
    });

    fetchSubmitBtn.addEventListener("click", async () => {
        const businessId = parseInt(fetchBusinessId.value);
        const businessNameVal = fetchBusinessName.value || fetchBusinessSearch.value.trim();
        const city = fetchCity.value.trim() || "Ottawa";

        if (!businessNameVal) {
            alert("Please enter or select a business name");
            return;
        }

        fetchStatus.textContent = "Searching the web for deals...";
        fetchStatus.className = "fetch-status active loading";

        try {
            const result = await scrapeDeals(businessId || 0, businessNameVal, city);
            if (result.status === "success") {
                fetchStatus.textContent = `Found and saved ${result.count} deal(s).`;
                fetchStatus.className = "fetch-status active success";
                loadDeals();
            } else {
                fetchStatus.textContent = "Failed to fetch deals: " + result.message;
                fetchStatus.className = "fetch-status active error";
            }
        } catch (error) {
            fetchStatus.textContent = "Error fetching deals from the web.";
            fetchStatus.className = "fetch-status active error";
        }
    });
});
