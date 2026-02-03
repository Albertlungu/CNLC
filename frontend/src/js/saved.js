import {
    requireAuth,
    logout,
    getSession,
    getUserCollections,
    getCollectionStats,
    createCollection,
    renameCollection,
    deleteCollection,
    getSavedBusinesses,
    unsaveBusiness,
    moveBusinessToCollection,
    getBusinessById,
} from "./api-client.js";
import { initNotifications } from "./notifications.js";

// Check authentication
if (!requireAuth()) {
    throw new Error("Authentication required");
}
initNotifications();

const session = getSession();
const userId = session.userId;

// State
let collections = [];
let savedBusinesses = [];
let allBusinessDetails = [];
let currentCollectionId = "all";
let filteredBusinesses = [];

// DOM Elements
const collectionList = document.getElementById("collection-list");
const collectionTitle = document.getElementById("collection-title");
const businessGrid = document.getElementById("business-grid");
const businessCountEl = document.getElementById("business-count");
const logoutBtn = document.getElementById("logout-btn");

const newCollectionBtn = document.getElementById("new-collection-btn");
const renameCollectionBtn = document.getElementById("rename-collection-btn");
const deleteCollectionBtn = document.getElementById("delete-collection-btn");

const searchInput = document.getElementById("search-input");
const searchBtn = document.getElementById("search-btn");
const categoryFilter = document.getElementById("category-filter");
const sortFilter = document.getElementById("sort-filter");

// Modals
const newCollectionModal = document.getElementById("new-collection-modal");
const renameCollectionModal = document.getElementById("rename-collection-modal");
const moveBusinessModal = document.getElementById("move-business-modal");

// Helper Functions
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

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    return date.toLocaleDateString();
}

// Load Collections
async function loadCollections() {
    try {
        const statsResult = await getCollectionStats(userId);
        if (statsResult.status === "success") {
            collections = statsResult.stats;
            renderCollectionList();
        }
    } catch (error) {
        console.error("Error loading collections:", error);
    }
}

function renderCollectionList() {
    const allSavedCount = savedBusinesses.length;

    const collectionsHTML = collections.map(col => `
        <div class="collection-item" data-collection-id="${col.collectionId}">
            <span class="collection-name">${col.name}</span>
            <span class="collection-count">${col.count}</span>
        </div>
    `).join("");

    collectionList.innerHTML = `
        <div class="collection-item all-saved active" data-collection-id="all">
            <span class="collection-name">All Saved</span>
            <span class="collection-count">${allSavedCount}</span>
        </div>
        ${collectionsHTML}
    `;

    // Add click listeners
    document.querySelectorAll(".collection-item").forEach(item => {
        item.addEventListener("click", () => {
            const collectionId = item.dataset.collectionId;
            switchCollection(collectionId);
        });
    });
}

function switchCollection(collectionId) {
    currentCollectionId = collectionId;

    // Update active state
    document.querySelectorAll(".collection-item").forEach(item => {
        item.classList.remove("active");
    });
    document.querySelector(`[data-collection-id="${collectionId}"]`).classList.add("active");

    // Update title and buttons
    if (collectionId === "all") {
        collectionTitle.textContent = "All Saved Businesses";
        renameCollectionBtn.style.display = "none";
        deleteCollectionBtn.style.display = "none";
    } else {
        const collection = collections.find(c => c.collectionId === parseInt(collectionId));
        collectionTitle.textContent = collection ? collection.name : "Collection";
        renameCollectionBtn.style.display = "block";
        deleteCollectionBtn.style.display = "block";
    }

    loadSavedBusinesses();
}

// Load Saved Businesses
async function loadSavedBusinesses() {
    try {
        const collectionId = currentCollectionId === "all" ? null : parseInt(currentCollectionId);
        const result = await getSavedBusinesses(userId, collectionId);

        if (result.status === "success") {
            savedBusinesses = result.savedBusinesses;

            // Fetch full business details
            allBusinessDetails = await Promise.all(
                savedBusinesses.map(async (saved) => {
                    const businessResult = await getBusinessById(saved.businessId);
                    if (businessResult.status === "success") {
                        return {
                            ...businessResult.business,
                            dateSaved: saved.dateSaved,
                            savedId: saved.savedId,
                            collectionId: saved.collectionId,
                        };
                    }
                    return null;
                })
            );

            allBusinessDetails = allBusinessDetails.filter(b => b !== null);

            // Update "All Saved" count
            if (currentCollectionId === "all") {
                const allSavedItem = document.querySelector('.collection-item.all-saved .collection-count');
                if (allSavedItem) {
                    allSavedItem.textContent = savedBusinesses.length;
                }
            }

            applyFilters();
        }
    } catch (error) {
        console.error("Error loading saved businesses:", error);
    }
}

function applyFilters() {
    const searchQuery = searchInput.value.toLowerCase();
    const category = categoryFilter.value;
    const sortBy = sortFilter.value;

    // Filter
    filteredBusinesses = allBusinessDetails.filter(business => {
        const matchesSearch = !searchQuery || business.name.toLowerCase().includes(searchQuery);
        const matchesCategory = !category || business.category === category;
        return matchesSearch && matchesCategory;
    });

    // Sort
    if (sortBy === "recent") {
        filteredBusinesses.sort((a, b) => new Date(b.dateSaved) - new Date(a.dateSaved));
    } else if (sortBy === "oldest") {
        filteredBusinesses.sort((a, b) => new Date(a.dateSaved) - new Date(b.dateSaved));
    } else if (sortBy === "name") {
        filteredBusinesses.sort((a, b) => a.name.localeCompare(b.name));
    }

    renderBusinessGrid();
}

function renderBusinessGrid() {
    businessCountEl.textContent = filteredBusinesses.length;

    if (filteredBusinesses.length === 0) {
        businessGrid.innerHTML = '<div class="no-results">No saved businesses found.</div>';
        return;
    }

    businessGrid.innerHTML = filteredBusinesses.map(business => {
        const addressText = formatAddress(business.address);
        const businessId = business.id || business.businessId;
        const categoryText = business.category ? `<span class="category-badge">${business.category}</span>` : "";
        const dateText = business.dateSaved ? `<div class="date-saved">Saved ${formatDate(business.dateSaved)}</div>` : "";

        return `
            <div class="business-card">
                <div class="business-card-header">
                    <h3>${business.name}</h3>
                    <div class="card-actions">
                        ${currentCollectionId !== "all" ? `<button class="icon-btn move-btn" data-business-id="${businessId}" data-business-name="${business.name}" title="Move to another collection">📁</button>` : ""}
                        <button class="icon-btn unsave-btn" data-business-id="${businessId}" title="Remove from saved">❌</button>
                    </div>
                </div>
                <p>${addressText}</p>
                ${categoryText}
                ${dateText}
                <a href="business-detail.html?id=${businessId}" class="view-details-link">View Details & Reviews</a>
            </div>
        `;
    }).join("");

    // Add event listeners
    document.querySelectorAll(".unsave-btn").forEach(btn => {
        btn.addEventListener("click", async (e) => {
            const businessId = parseInt(e.target.dataset.businessId);
            await handleUnsave(businessId);
        });
    });

    document.querySelectorAll(".move-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const businessId = parseInt(e.target.dataset.businessId);
            const businessName = e.target.dataset.businessName;
            openMoveBusinessModal(businessId, businessName);
        });
    });
}

// Unsave Business
async function handleUnsave(businessId) {
    if (!confirm("Remove this business from saved?")) return;

    try {
        const collectionId = currentCollectionId === "all" ? null : parseInt(currentCollectionId);
        const result = await unsaveBusiness(userId, businessId, collectionId);

        if (result.status === "success") {
            await loadCollections();
            await loadSavedBusinesses();
        } else {
            alert("Failed to remove business: " + result.message);
        }
    } catch (error) {
        console.error("Error unsaving business:", error);
        alert("An error occurred while removing the business.");
    }
}

// Collection Management
newCollectionBtn.addEventListener("click", () => {
    newCollectionModal.classList.add("active");
    document.getElementById("collection-name-input").value = "";
    document.getElementById("collection-name-input").focus();
});

document.getElementById("close-new-collection").addEventListener("click", () => {
    newCollectionModal.classList.remove("active");
});

document.getElementById("cancel-new-collection-btn").addEventListener("click", () => {
    newCollectionModal.classList.remove("active");
});

document.getElementById("create-collection-btn").addEventListener("click", async () => {
    const name = document.getElementById("collection-name-input").value.trim();
    if (!name) {
        alert("Please enter a collection name.");
        return;
    }

    try {
        const result = await createCollection(userId, name);
        if (result.status === "success") {
            newCollectionModal.classList.remove("active");
            await loadCollections();
        } else {
            alert("Failed to create collection: " + result.message);
        }
    } catch (error) {
        console.error("Error creating collection:", error);
        alert("An error occurred while creating the collection.");
    }
});

// Rename Collection
renameCollectionBtn.addEventListener("click", () => {
    const collection = collections.find(c => c.collectionId === parseInt(currentCollectionId));
    if (!collection) return;

    renameCollectionModal.classList.add("active");
    document.getElementById("rename-collection-input").value = collection.name;
    document.getElementById("rename-collection-input").focus();
});

document.getElementById("close-rename-collection").addEventListener("click", () => {
    renameCollectionModal.classList.remove("active");
});

document.getElementById("cancel-rename-btn").addEventListener("click", () => {
    renameCollectionModal.classList.remove("active");
});

document.getElementById("confirm-rename-btn").addEventListener("click", async () => {
    const newName = document.getElementById("rename-collection-input").value.trim();
    if (!newName) {
        alert("Please enter a new name.");
        return;
    }

    try {
        const result = await renameCollection(userId, parseInt(currentCollectionId), newName);
        if (result.status === "success") {
            renameCollectionModal.classList.remove("active");
            await loadCollections();
            switchCollection(currentCollectionId);
        } else {
            alert("Failed to rename collection: " + result.message);
        }
    } catch (error) {
        console.error("Error renaming collection:", error);
        alert("An error occurred while renaming the collection.");
    }
});

// Delete Collection
deleteCollectionBtn.addEventListener("click", async () => {
    const collection = collections.find(c => c.collectionId === parseInt(currentCollectionId));
    if (!collection) return;

    if (!confirm(`Delete "${collection.name}" and all businesses in it?`)) return;

    try {
        const result = await deleteCollection(userId, parseInt(currentCollectionId));
        if (result.status === "success") {
            currentCollectionId = "all";
            await loadCollections();
            await loadSavedBusinesses();
        } else {
            alert("Failed to delete collection: " + result.message);
        }
    } catch (error) {
        console.error("Error deleting collection:", error);
        alert("An error occurred while deleting the collection.");
    }
});

// Move Business
function openMoveBusinessModal(businessId, businessName) {
    moveBusinessModal.classList.add("active");
    document.getElementById("move-business-name").textContent = `Move "${businessName}" to:`;

    const select = document.getElementById("move-collection-select");
    select.innerHTML = collections
        .filter(c => c.collectionId !== parseInt(currentCollectionId))
        .map(c => `<option value="${c.collectionId}">${c.name}</option>`)
        .join("");

    select.dataset.businessId = businessId;
}

document.getElementById("close-move-business").addEventListener("click", () => {
    moveBusinessModal.classList.remove("active");
});

document.getElementById("cancel-move-btn").addEventListener("click", () => {
    moveBusinessModal.classList.remove("active");
});

document.getElementById("confirm-move-btn").addEventListener("click", async () => {
    const select = document.getElementById("move-collection-select");
    const businessId = parseInt(select.dataset.businessId);
    const newCollectionId = parseInt(select.value);

    if (!newCollectionId) {
        alert("Please select a collection.");
        return;
    }

    try {
        const result = await moveBusinessToCollection(userId, businessId, parseInt(currentCollectionId), newCollectionId);
        if (result.status === "success") {
            moveBusinessModal.classList.remove("active");
            await loadCollections();
            await loadSavedBusinesses();
        } else {
            alert("Failed to move business: " + result.message);
        }
    } catch (error) {
        console.error("Error moving business:", error);
        alert("An error occurred while moving the business.");
    }
});

// Filter Event Listeners
searchBtn.addEventListener("click", applyFilters);
searchInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") applyFilters();
});
categoryFilter.addEventListener("change", applyFilters);
sortFilter.addEventListener("change", applyFilters);

// Logout
if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
        e.preventDefault();
        logout();
    });
}

// Initialize
async function init() {
    await loadCollections();
    await loadSavedBusinesses();
}

init();
