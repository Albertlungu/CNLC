import { requireAuth, logout, getSession, getTrending, uploadReceipt, getBusinessById, filterBusinesses } from "./api-client.js";

if (!requireAuth()) {
    throw new Error("Authentication required");
}

const session = getSession();
const userId = session.userId;

const trendingList = document.getElementById("trending-list");
const uploadBtn = document.getElementById("upload-receipt-btn");
const logoutBtn = document.getElementById("logout-btn");

// Modal elements
const receiptModal = document.getElementById("receipt-modal");
const receiptClose = document.getElementById("receipt-close");
const receiptForm = document.getElementById("receipt-form");
const businessSearchInput = document.getElementById("receipt-business-search");
const searchResults = document.getElementById("receipt-search-results");
const businessIdInput = document.getElementById("receipt-business-id");
const receiptImageInput = document.getElementById("receipt-image");
const receiptPreview = document.getElementById("receipt-preview");

let searchTimeout = null;

// Cache business names to avoid repeated API calls
const businessNameCache = {};

async function getBusinessName(businessId) {
    if (businessNameCache[businessId]) return businessNameCache[businessId];
    try {
        const result = await getBusinessById(businessId);
        if (result.status === "success" && result.business) {
            businessNameCache[businessId] = result.business;
            return result.business;
        }
    } catch (e) { /* ignore */ }
    return null;
}

// Populate the top 3 podium cards
function populatePodiumCard(rank, trending, business) {
    const card = document.getElementById(`podium-${rank}`);
    if (!card) return;

    const name = business ? business.name : `Business #${trending.businessId}`;
    const category = business ? (business.category || "") : "";
    const meta = `${trending.receiptCount} receipt${trending.receiptCount !== 1 ? 's' : ''} - $${trending.totalSpent.toFixed(2)} total`;

    card.href = `business-detail.html?id=${trending.businessId}`;
    card.querySelector(".podium-name").textContent = name;
    card.querySelector(".podium-category").textContent = category;
    card.querySelector(".podium-points").textContent = trending.points.toFixed(1);
    card.querySelector(".podium-meta").textContent = meta;
}

async function loadTrending() {
    trendingList.innerHTML = '<div class="loading">Loading trending businesses...</div>';

    try {
        const result = await getTrending(50);
        if (result.status !== "success" || result.trending.length === 0) {
            trendingList.innerHTML = '<div class="no-trending">No trending businesses yet. Be the first to upload a receipt.</div>';
            return;
        }

        // Find max points for bar scaling
        const maxPoints = Math.max(...result.trending.map(t => t.points), 1);

        // Populate podium (top 3)
        for (let i = 0; i < Math.min(3, result.trending.length); i++) {
            const t = result.trending[i];
            const business = await getBusinessName(t.businessId);
            populatePodiumCard(i + 1, t, business);
        }

        trendingList.innerHTML = "";

        for (let i = 3; i < result.trending.length; i++) {
            const t = result.trending[i];
            const business = await getBusinessName(t.businessId);
            const name = business ? business.name : `Business #${t.businessId}`;
            const category = business ? (business.category || "") : "";
            const barWidth = Math.min((t.points / maxPoints) * 100, 100);

            const item = document.createElement("div");
            item.className = "trending-item";
            item.innerHTML = `
                <div class="trending-rank">#${i + 1}</div>
                <div class="trending-info">
                    <div class="trending-name">
                        <a href="business-detail.html?id=${t.businessId}">${name}</a>
                    </div>
                    ${category ? `<div class="trending-category">${category}</div>` : ""}
                </div>
                <div class="trending-stats">
                    <div class="trending-points">${t.points.toFixed(1)}</div>
                    <div class="trending-points-label">points</div>
                    <div class="points-bar-container">
                        <div class="points-bar" style="width: ${barWidth}%"></div>
                    </div>
                    <div class="trending-meta">${t.receiptCount} receipt${t.receiptCount !== 1 ? 's' : ''} - $${t.totalSpent.toFixed(2)} total</div>
                </div>
            `;
            trendingList.appendChild(item);
        }
    } catch (error) {
        console.error("Error loading trending:", error);
        trendingList.innerHTML = '<div class="no-trending">Failed to load trending data.</div>';
    }
}

// Business search
async function searchBusinesses(query) {
    if (query.length < 2) {
        searchResults.classList.remove("active");
        return;
    }

    try {
        const result = await filterBusinesses(query, null, null, null, null, null, 0, 8);
        if (result.status === "success" && result.businesses.length > 0) {
            searchResults.innerHTML = result.businesses.map(b =>
                `<div class="search-dropdown-item" data-id="${b.id || b.businessId}" data-name="${b.name}">${b.name}</div>`
            ).join("");
            searchResults.classList.add("active");

            searchResults.querySelectorAll(".search-dropdown-item").forEach(item => {
                item.addEventListener("click", () => {
                    businessIdInput.value = item.dataset.id;
                    businessSearchInput.value = item.dataset.name;
                    searchResults.classList.remove("active");
                });
            });
        } else {
            searchResults.classList.remove("active");
        }
    } catch (e) {
        searchResults.classList.remove("active");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadTrending();

    if (logoutBtn) {
        logoutBtn.addEventListener("click", (e) => {
            e.preventDefault();
            logout();
        });
    }

    // Modal
    uploadBtn.addEventListener("click", () => receiptModal.classList.add("active"));
    receiptClose.addEventListener("click", () => receiptModal.classList.remove("active"));
    receiptModal.addEventListener("click", (e) => { if (e.target === receiptModal) receiptModal.classList.remove("active"); });

    // Business search
    businessSearchInput.addEventListener("input", () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => searchBusinesses(businessSearchInput.value.trim()), 300);
    });

    // Image preview
    receiptImageInput.addEventListener("change", () => {
        const file = receiptImageInput.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                receiptPreview.innerHTML = `<img src="${e.target.result}" alt="Receipt preview">`;
            };
            reader.readAsDataURL(file);
        } else {
            receiptPreview.innerHTML = "";
        }
    });

    // Submit receipt
    receiptForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const businessId = parseInt(businessIdInput.value);
        if (!businessId) {
            alert("Please select a business");
            return;
        }

        const amount = parseFloat(document.getElementById("receipt-amount").value);
        if (!amount || amount <= 0) {
            alert("Please enter a valid amount");
            return;
        }

        const imageFile = receiptImageInput.files[0];
        if (!imageFile) {
            alert("Please upload a receipt image");
            return;
        }

        try {
            const result = await uploadReceipt(userId, businessId, amount, imageFile);
            if (result.status === "success") {
                receiptModal.classList.remove("active");
                receiptForm.reset();
                receiptPreview.innerHTML = "";
                businessIdInput.value = "";
                loadTrending();
            } else {
                alert("Failed to submit receipt: " + result.message);
            }
        } catch (error) {
            console.error("Error uploading receipt:", error);
            alert("An error occurred while uploading the receipt.");
        }
    });
});