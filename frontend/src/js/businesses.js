import { filterBusinesses, requireAuth, logout, getSession, checkBusinessSaved, saveBusiness, unsaveBusiness, getUserCollections, createCollection, getRecommendations } from "./api-client.js";
import { getUserLocation } from "./utils/helper.js";
import { initNotifications } from "./notifications.js";

// Check authentication before loading page
if (!requireAuth()) {
    throw new Error("Authentication required");
}
initNotifications();

const session = getSession();
const userId = session.userId;

const filterState = {
    searchQuery: "",
    categories: [],
    ratings: [],
    radius: null,
};

const grid = document.getElementById("business-grid");
const prevPageBtn = document.getElementById("prev-page");
const nextPageBtn = document.getElementById("next-page");
const searchInput = document.getElementById("search-input");
const searchBtn = document.getElementById("search-btn");
const logoutBtn = document.getElementById("logout-btn");

// Collection Modal Elements
const collectionModal = document.getElementById("collection-modal");
const modalTitle = document.getElementById("modal-title");
const modalBusinessName = document.getElementById("modal-business-name");
const collectionList = document.getElementById("collection-list");
const modalCancelBtn = document.getElementById("modal-cancel-btn");
const modalConfirmBtn = document.getElementById("modal-confirm-btn");
const modalClose = document.querySelector(".modal-close");

let currentPage = 1;
let totalResults = 0;
const businessesPerPage = 30;
let selectedCollectionId = null;
let pendingSaveBusinessId = null;
let pendingSaveBtn = null;



function formatAddress(address) {
    if (!address) return "Address not available";
    const parts = [];
    if (address.housenumber) parts.push(address.housenumber);
    if (address.street) parts.push(address.street);
    const streetLine = parts.join(" ");
    if (streetLine && address.city) {
        return `${streetLine}, ${address.city}`;
    }
    if (address.city) return address.city;
    return streetLine || "Address not available";
}

async function createBusinessCard(business) {
    const box = document.createElement("div");
    box.className = "business-box";

    const addressText = formatAddress(business.address);
    const categoryText = business.category ? `Category: ${business.category}` : "";
    const businessId = business.id || business.businessId;

    // Check if business is saved
    let isSaved = false;
    try {
        const savedResult = await checkBusinessSaved(userId, businessId);
        isSaved = savedResult.saved;
    } catch (error) {
        console.error("Error checking saved status:", error);
    }

    box.innerHTML = `
    <div class="dropdown-bar">
      ${business.name}
      <div class="bar-actions">
        <button class="save-btn ${isSaved ? 'saved' : ''}" data-business-id="${businessId}" title="${isSaved ? 'Saved' : 'Save to collection'}">
          ${isSaved ? '★' : '☆'}
        </button>
        <span class="arrow">&#9662;</span>
      </div>
    </div>
    <div class="description">
        ${addressText}
        ${categoryText ? `<br><span class="category-tag">${categoryText}</span>` : ""}
        <br><a href="business-detail.html?id=${businessId}" class="view-details-link">View Details & Reviews</a>
    </div>
  `;

    const bar = box.querySelector(".dropdown-bar");
    const arrow = bar.querySelector(".arrow");
    const desc = box.querySelector(".description");
    const saveBtn = box.querySelector(".save-btn");

    bar.addEventListener("click", (e) => {
        if (e.target.classList.contains("save-btn") || e.target.closest(".save-btn")) {
            return;
        }
        desc.classList.toggle("show");
        arrow.classList.toggle("rotate");
    });

    saveBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const businessId = parseInt(saveBtn.dataset.businessId);

        if (saveBtn.classList.contains("saved")) {
            await handleUnsave(businessId, saveBtn);
        } else {
            await handleSave(businessId, business.name, saveBtn);
        }
    });

    return box;
}

async function renderPage(page) {
    console.log("renderPage called with page:", page);
    grid.style.opacity = 0;

    let lat = null;
    let lon = null;

    if (filterState.radius) {
        console.log("Radius filter active, attempting to get location...");
        try {
            const location = await getUserLocation();
            lat = location.lat;
            lon = location.lon;
            console.log("Got location:", lat, lon);
        } catch (error) {
            console.error("Could not fetch location:", error);
            console.log("Continuing without location");
        }
    }

    const radiusInt = filterState.radius ? parseInt(filterState.radius, 10) : null;
    const minRating = filterState.ratings.length > 0 ? Math.min(...filterState.ratings) : null;

    console.log("Calling API with:", {
        search: filterState.searchQuery,
        category: filterState.categories[0],
        lat,
        lon,
        radius: radiusInt,
        minRating,
        page
    });

    try {
        const offset = (page - 1) * businessesPerPage;
        const result = await filterBusinesses(
            filterState.searchQuery,
            filterState.categories[0],
            lat,
            lon,
            radiusInt,
            minRating,
            offset,
            businessesPerPage
        );
        console.log("API Response:", result);
        console.log("Number of businesses:", result.businesses?.length);

        if (result.status === 'success') {
            grid.innerHTML = "";
            totalResults = result.total || 0;

            if (result.businesses.length === 0) {
                grid.innerHTML = '<div class="no-results">No businesses found matching your criteria.</div>';
            } else {
                for (const business of result.businesses) {
                    const card = await createBusinessCard(business);
                    grid.appendChild(card);
                }
            }

            updatePaginationButtons();
            grid.style.opacity = 1;
        } else {
            console.error("API did not return success status");
            showError("Failed to load businesses. Please try again.");
        }
    } catch (e) {
        console.error("Error rendering businesses: ", e);
        showError("An error occurred while loading businesses.");
    }
}

function showError(message) {
    grid.innerHTML = `<div class="error-message">${message}</div>`;
    grid.style.opacity = 1;
}

function updatePaginationButtons() {
    const totalPages = Math.ceil(totalResults / businessesPerPage);
    prevPageBtn.disabled = currentPage <= 1;
    nextPageBtn.disabled = currentPage >= totalPages || totalResults === 0;
}

function createHeartParticles(heart) {
    for (let i = 0; i < 8; i++) {
        const particle = document.createElement("div");
        particle.className = "particle";

        const angle = i * 45 * (Math.PI / 180);
        const distance = 20 + Math.random() * 10;
        particle.style.setProperty("--x", `${Math.cos(angle) * distance}px`);
        particle.style.setProperty("--y", `${Math.sin(angle) * distance}px`);

        particle.style.left = "50%";
        particle.style.top = "50%";
        particle.style.transform = "translate(-50%, -50%)";

        heart.appendChild(particle);
        particle.addEventListener("animationend", () => particle.remove());
    }
}


function toggleFilter(headerElement) {
    const filterGroup = headerElement.parentElement;
    const content = filterGroup.querySelector(".filter-content");
    const isActive = headerElement.classList.contains("active");

    document.querySelectorAll(".filter-header").forEach((header) => {
        header.classList.remove("active");
    });
    document.querySelectorAll(".filter-content").forEach((c) => {
        c.classList.remove("active");
    });

    if (!isActive) {
        headerElement.classList.add("active");
        content.classList.add("active");
    }
}

document.addEventListener("DOMContentLoaded", function () {
    initializeFilters();
    setupEventListeners();
    setupSearchListeners();
    setupModalListeners();
    setupSearchHistoryTracking();
    logFilterState();

    // Load recommendations (non-blocking)
    loadRecommendations();

    // Load businesses
    renderPage(currentPage);

    prevPageBtn.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            renderPage(currentPage);
        }
    });

    nextPageBtn.addEventListener("click", () => {
        const totalPages = Math.ceil(totalResults / businessesPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            renderPage(currentPage);
        }
    });

    // Logout button handler
    if (logoutBtn) {
        logoutBtn.addEventListener("click", (e) => {
            e.preventDefault();
            logout();
        });
    }
});

function setupModalListeners() {
    modalCancelBtn.addEventListener('click', closeCollectionModal);
    modalClose.addEventListener('click', closeCollectionModal);
    modalConfirmBtn.addEventListener('click', confirmSaveToCollection);

    // Close modal when clicking outside
    collectionModal.addEventListener('click', (e) => {
        if (e.target === collectionModal) {
            closeCollectionModal();
        }
    });
}

function setupSearchListeners() {
    searchBtn.addEventListener("click", () => {
        filterState.searchQuery = searchInput.value.trim();
        currentPage = 1;
        renderPage(currentPage);
    });

    searchInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            filterState.searchQuery = searchInput.value.trim();
            currentPage = 1;
            renderPage(currentPage);
        }
    });
}

function initializeFilters() {
    // Filters initialized via HTML defaults
}

function setupEventListeners() {
    const filterHeaders = document.querySelectorAll(".filter-header");
    filterHeaders.forEach((header) => {
        header.addEventListener("click", function () {
            toggleFilter(this);
        });
    });

    const categoryCheckboxes = document.querySelectorAll(".category");
    categoryCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", function (e) {
            if (e.target.checked) {
                filterState.categories.push(e.target.value);
            } else {
                filterState.categories = filterState.categories.filter(
                    (cat) => cat !== e.target.value,
                );
            }
            console.log("Categories updated:", filterState.categories);
            currentPage = 1;
            logFilterState();
            renderPage(currentPage);
        });
    });

    const ratingCheckboxes = document.querySelectorAll(".rating");
    ratingCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", function (e) {
            if (e.target.checked) {
                filterState.ratings.push(parseInt(e.target.value));
            } else {
                filterState.ratings = filterState.ratings.filter(
                    (rating) => rating !== parseInt(e.target.value),
                );
            }
            filterState.ratings.sort((a, b) => a - b);
            console.log("Ratings updated:", filterState.ratings);
            currentPage = 1;
            logFilterState();
            renderPage(currentPage);
        });
    });

    const radiusRadios = document.querySelectorAll('input[name="radius"]');
    radiusRadios.forEach((radio) => {
        radio.addEventListener("change", function (e) {
            if (e.target.checked) {
                filterState.radius = parseInt(e.target.value, 10);
                console.log("Radius changed:", filterState.radius);
                currentPage = 1;
                logFilterState();
                renderPage(currentPage);
            }
        });
    });
}

function logFilterState() {
    console.log("=== Current Filter State ===");
    console.log("Search:", filterState.searchQuery);
    console.log("Categories:", filterState.categories);
    console.log("Ratings:", filterState.ratings);
    console.log("Radius:", filterState.radius);
    console.log("==========================");
}

function getFilterState() {
    return JSON.parse(JSON.stringify(filterState));
}

function resetFilters() {
    filterState.searchQuery = "";
    if (searchInput) searchInput.value = "";

    filterState.categories = [];
    document.querySelectorAll(".category").forEach((cb) => (cb.checked = false));

    filterState.ratings = [];
    document.querySelectorAll(".rating").forEach((cb) => (cb.checked = false));

    filterState.radius = null;
    document.querySelectorAll('input[name="radius"]').forEach((radio) => (radio.checked = false));

    currentPage = 1;
    console.log("Filters reset to default state");
    logFilterState();
}

function applyFilters() {
    console.log("Applying filters with state:", getFilterState());
}

// Modal Functions
function openCollectionModal(businessId, businessName, collections, saveBtn) {
    pendingSaveBusinessId = businessId;
    pendingSaveBtn = saveBtn;
    selectedCollectionId = collections[0].collectionId; // Default to first collection

    modalBusinessName.textContent = `Save "${businessName}" to:`;

    collectionList.innerHTML = collections.map(c => `
        <div class="collection-option ${c.collectionId === selectedCollectionId ? 'selected' : ''}" data-collection-id="${c.collectionId}">
            ${c.name}
        </div>
    `).join('');

    // Add click listeners to collection options
    document.querySelectorAll('.collection-option').forEach(option => {
        option.addEventListener('click', () => {
            selectedCollectionId = parseInt(option.dataset.collectionId);
            document.querySelectorAll('.collection-option').forEach(opt => opt.classList.remove('selected'));
            option.classList.add('selected');
        });
    });

    collectionModal.classList.add('active');
}

function closeCollectionModal() {
    collectionModal.classList.remove('active');
    selectedCollectionId = null;
    pendingSaveBusinessId = null;
    pendingSaveBtn = null;
}

async function confirmSaveToCollection() {
    if (!selectedCollectionId || !pendingSaveBusinessId || !pendingSaveBtn) return;

    try {
        const result = await saveBusiness(userId, pendingSaveBusinessId, selectedCollectionId);
        if (result.status === "success") {
            pendingSaveBtn.classList.add("saved");
            pendingSaveBtn.textContent = "★";
            pendingSaveBtn.title = "Saved";
            closeCollectionModal();
        } else {
            alert("Failed to save: " + result.message);
        }
    } catch (error) {
        console.error("Error saving business:", error);
        alert("An error occurred while saving the business.");
    }
}

// Save/Unsave Handlers
async function handleSave(businessId, businessName, saveBtn) {
    try {
        let collectionsResult = await getUserCollections(userId);
        let collections = collectionsResult.status === "success" ? collectionsResult.collections : [];

        // Auto-create "Favorites" collection if user has none
        if (collections.length === 0) {
            const createResult = await createCollection(userId, "Favorites");
            if (createResult.status === "success") {
                collections = [createResult.collection];
            } else {
                alert("Failed to create default collection: " + createResult.message);
                return;
            }
        }

        if (collections.length === 1) {
            // If only one collection, save directly
            const result = await saveBusiness(userId, businessId, collections[0].collectionId);
            if (result.status === "success") {
                saveBtn.classList.add("saved");
                saveBtn.textContent = "★";
                saveBtn.title = "Saved";
            } else {
                alert("Failed to save: " + result.message);
            }
        } else {
            // Show collection selection modal
            openCollectionModal(businessId, businessName, collections, saveBtn);
        }
    } catch (error) {
        console.error("Error saving business:", error);
        alert("An error occurred while saving the business.");
    }
}

async function handleUnsave(businessId, saveBtn) {
    try {
        const result = await unsaveBusiness(userId, businessId);
        if (result.status === "success") {
            saveBtn.classList.remove("saved");
            saveBtn.textContent = "☆";
            saveBtn.title = "Save to collection";
        } else {
            alert("Failed to unsave: " + result.message);
        }
    } catch (error) {
        console.error("Error unsaving business:", error);
        alert("An error occurred while removing the business.");
    }
}

// ==================== AI Recommendations ====================
async function loadRecommendations() {
    try {
        const searchHistory = JSON.parse(localStorage.getItem("searchHistory") || "[]");
        const result = await getRecommendations(userId, searchHistory);
        if (result.status === "success" && result.recommendations && result.recommendations.length > 0) {
            const section = document.getElementById("recommendations-section");
            const recGrid = document.getElementById("recommendations-grid");
            if (section && recGrid) {
                section.style.display = "block";
                recGrid.innerHTML = result.recommendations.map(rec => `
                    <div class="recommendation-card" onclick="window.location.href='business-detail.html?id=${rec.businessId}'">
                        <div class="rec-name">${rec.businessName || "Business"}</div>
                        <div class="rec-category">${rec.category || ""}</div>
                        <div class="rec-reason">${rec.reason || ""}</div>
                    </div>
                `).join("");
            }
        }
    } catch (err) {
        console.error("Recommendations error:", err);
        // Silently fail - recommendations are optional
    }
}

// Track search history in localStorage
function setupSearchHistoryTracking() {
    if (searchInput) {
        searchInput.addEventListener("change", () => {
            const query = searchInput.value.trim();
            if (query) {
                const history = JSON.parse(localStorage.getItem("searchHistory") || "[]");
                if (!history.includes(query)) {
                    history.unshift(query);
                    localStorage.setItem("searchHistory", JSON.stringify(history.slice(0, 20)));
                }
            }
        });
    }
}

if (typeof module !== "undefined" && module.exports) {
    module.exports = {
        getFilterState,
        resetFilters,
        applyFilters,
    };
}
