import { filterBusinesses, requireAuth, logout, getSession, checkBusinessSaved, saveBusiness, unsaveBusiness, getUserCollections, createCollection } from "./api-client.js";
import { initNotifications } from "./notifications.js";

if (!requireAuth()) {
    throw new Error("Authentication required");
}
initNotifications();

const session = getSession();
const userId = session.userId;

const DEFAULT_CENTER = [45.4215, -75.6972];
const DEFAULT_ZOOM = 13;

let map;
let markers = [];
let allBusinesses = [];
let filteredBusinesses = [];

const businessListEl = document.getElementById("business-list");
const visibleCountEl = document.getElementById("visible-count");
const mapSearchInput = document.getElementById("map-search");
const searchBtn = document.getElementById("search-btn");
const categoryFilter = document.getElementById("category-filter");
const locateMeBtn = document.getElementById("locate-me");
const resetViewBtn = document.getElementById("reset-view");
const logoutBtn = document.getElementById("logout-btn");

const modal = document.getElementById("street-view-modal");
const modalBusinessName = document.getElementById("modal-business-name");
const modalAddress = document.getElementById("modal-address");
const modalCategory = document.getElementById("modal-category");
const streetViewLink = document.getElementById("street-view-link");
const directionsLink = document.getElementById("directions-link");
const detailLink = document.getElementById("detail-link");
const closeModalBtn = document.querySelector(".close-modal");

function initMap() {
    map = L.map("map").setView(DEFAULT_CENTER, DEFAULT_ZOOM);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
    }).addTo(map);

    map.on("moveend", updateVisibleBusinesses);
}

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

function createCustomIcon() {
    return L.divIcon({
        className: "custom-div-icon",
        html: `<div style="
            background: #ff6600;
            border: 3px solid white;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        "></div>`,
        iconSize: [26, 26],
        iconAnchor: [13, 13],
    });
}

async function createPopupContent(business) {
    const addressText = formatAddress(business.address);
    const businessId = business.id || business.businessId;
    const lat = business.latitude;
    const lon = business.longitude;

    // Check if business is saved
    let isSaved = false;
    try {
        const savedResult = await checkBusinessSaved(userId, businessId);
        isSaved = savedResult.saved;
    } catch (error) {
        console.error("Error checking saved status:", error);
    }

    return `
        <div class="popup-content">
            <h3>${business.name}</h3>
            <p>${addressText}</p>
            ${business.category ? `<span class="popup-category">${business.category}</span>` : ""}
            <div class="popup-actions">
                <button class="popup-btn save-popup-btn ${isSaved ? 'saved' : ''}"
                        data-business-id="${businessId}"
                        data-business-name="${business.name}"
                        title="${isSaved ? 'Saved' : 'Save to collection'}">
                    ${isSaved ? '★ Saved' : '☆ Save'}
                </button>
                <a href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${lat},${lon}"
                   target="_blank" class="popup-btn street-view">Street View</a>
                <a href="https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}"
                   target="_blank" class="popup-btn directions">Directions</a>
                <a href="business-detail.html?id=${businessId}" class="popup-btn details">Reviews</a>
            </div>
        </div>
    `;
}

async function addMarkers(businesses) {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];

    for (const business of businesses) {
        if (business.latitude && business.longitude) {
            const marker = L.marker([business.latitude, business.longitude], {
                icon: createCustomIcon(),
            });

            const popupContent = await createPopupContent(business);
            marker.bindPopup(popupContent, {
                maxWidth: 300,
                className: "custom-popup",
            });

            marker.businessData = business;

            marker.on("click", () => {
                highlightBusinessInList(business);
            });

            marker.on("popupopen", () => {
                setupPopupSaveButton();
            });

            marker.addTo(map);
            markers.push(marker);
        }
    }
}

function setupPopupSaveButton() {
    const saveBtn = document.querySelector(".save-popup-btn");
    if (saveBtn) {
        saveBtn.addEventListener("click", async (e) => {
            e.preventDefault();
            const businessId = parseInt(saveBtn.dataset.businessId);
            const businessName = saveBtn.dataset.businessName;

            if (saveBtn.classList.contains("saved")) {
                await handleUnsaveMap(businessId, businessName, saveBtn);
            } else {
                await handleSaveMap(businessId, businessName, saveBtn);
            }
        });
    }
}

function highlightBusinessInList(business) {
    document.querySelectorAll(".business-item").forEach(item => {
        item.classList.remove("active");
    });

    const businessId = business.id || business.businessId;
    const item = document.querySelector(`.business-item[data-id="${businessId}"]`);
    if (item) {
        item.classList.add("active");
        item.scrollIntoView({ behavior: "smooth", block: "center" });
    }
}

function renderBusinessList(businesses) {
    if (businesses.length === 0) {
        businessListEl.innerHTML = '<div class="loading">No businesses found in this area.</div>';
        visibleCountEl.textContent = "0";
        return;
    }

    visibleCountEl.textContent = businesses.length.toString();

    businessListEl.innerHTML = businesses.map(business => {
        const addressText = formatAddress(business.address);
        const businessId = business.id || business.businessId;

        return `
            <div class="business-item" data-id="${businessId}" data-lat="${business.latitude}" data-lon="${business.longitude}">
                <h4>${business.name}</h4>
                <p>${addressText}</p>
                ${business.category ? `<span class="category-badge">${business.category}</span>` : ""}
            </div>
        `;
    }).join("");

    document.querySelectorAll(".business-item").forEach(item => {
        item.addEventListener("click", () => {
            const lat = parseFloat(item.dataset.lat);
            const lon = parseFloat(item.dataset.lon);
            const businessId = item.dataset.id;

            if (lat && lon) {
                map.setView([lat, lon], 17);

                const marker = markers.find(m => {
                    const bid = m.businessData.id || m.businessData.businessId;
                    return bid.toString() === businessId;
                });

                if (marker) {
                    marker.openPopup();
                }
            }

            document.querySelectorAll(".business-item").forEach(i => i.classList.remove("active"));
            item.classList.add("active");
        });
    });
}

function updateVisibleBusinesses() {
    const bounds = map.getBounds();
    const visible = filteredBusinesses.filter(business => {
        if (!business.latitude || !business.longitude) return false;
        return bounds.contains([business.latitude, business.longitude]);
    });

    renderBusinessList(visible);
}

async function loadBusinesses() {
    businessListEl.innerHTML = '<div class="loading">Loading businesses...</div>';

    try {
        const result = await filterBusinesses(null, null, null, null, null, null, 0, 5000);

        if (result.status === "success") {
            allBusinesses = result.businesses.filter(b => b.latitude && b.longitude);
            filteredBusinesses = [...allBusinesses];

            addMarkers(filteredBusinesses);

            if (allBusinesses.length > 0) {
                const bounds = L.latLngBounds(allBusinesses.map(b => [b.latitude, b.longitude]));
                map.fitBounds(bounds, { padding: [50, 50] });
            }

            updateVisibleBusinesses();
        } else {
            businessListEl.innerHTML = '<div class="loading">Failed to load businesses.</div>';
        }
    } catch (error) {
        console.error("Error loading businesses:", error);
        businessListEl.innerHTML = '<div class="loading">Error loading businesses.</div>';
    }
}

function applyFilters() {
    const searchTerm = mapSearchInput.value.trim().toLowerCase();
    const category = categoryFilter.value;

    filteredBusinesses = allBusinesses.filter(business => {
        const matchesSearch = !searchTerm ||
            business.name.toLowerCase().includes(searchTerm) ||
            (business.category && business.category.toLowerCase().includes(searchTerm));

        const matchesCategory = !category || business.category === category;

        return matchesSearch && matchesCategory;
    });

    addMarkers(filteredBusinesses);
    updateVisibleBusinesses();
}

function locateUser() {
    if (!navigator.geolocation) {
        alert("Geolocation is not supported by your browser.");
        return;
    }

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;

            map.setView([lat, lon], 15);

            L.circleMarker([lat, lon], {
                radius: 10,
                fillColor: "#4285f4",
                color: "#fff",
                weight: 3,
                opacity: 1,
                fillOpacity: 0.8,
            }).addTo(map).bindPopup("You are here").openPopup();
        },
        (error) => {
            console.error("Error getting location:", error);
            alert("Unable to get your location. Please enable location services.");
        }
    );
}

function openBusinessModal(business) {
    const addressText = formatAddress(business.address);
    const businessId = business.id || business.businessId;
    const lat = business.latitude;
    const lon = business.longitude;

    modalBusinessName.textContent = business.name;
    modalAddress.textContent = addressText;
    modalCategory.textContent = business.category ? `Category: ${business.category}` : "";

    streetViewLink.href = `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${lat},${lon}`;
    directionsLink.href = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}`;
    detailLink.href = `business-detail.html?id=${businessId}`;

    modal.classList.add("active");
}

function closeModal() {
    modal.classList.remove("active");
}

function setupEventListeners() {
    searchBtn.addEventListener("click", applyFilters);

    mapSearchInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            applyFilters();
        }
    });

    categoryFilter.addEventListener("change", applyFilters);

    locateMeBtn.addEventListener("click", locateUser);

    resetViewBtn.addEventListener("click", () => {
        if (allBusinesses.length > 0) {
            const bounds = L.latLngBounds(allBusinesses.map(b => [b.latitude, b.longitude]));
            map.fitBounds(bounds, { padding: [50, 50] });
        } else {
            map.setView(DEFAULT_CENTER, DEFAULT_ZOOM);
        }
    });

    closeModalBtn.addEventListener("click", closeModal);

    modal.addEventListener("click", (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    if (logoutBtn) {
        logoutBtn.addEventListener("click", (e) => {
            e.preventDefault();
            logout();
        });
    }
}

// Save/Unsave Map Handlers
async function handleSaveMap(businessId, businessName, saveBtn) {
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
            const result = await saveBusiness(userId, businessId, collections[0].collectionId);
            if (result.status === "success") {
                saveBtn.classList.add("saved");
                saveBtn.textContent = "★ Saved";
                saveBtn.title = "Saved";
            } else {
                alert("Failed to save: " + result.message);
            }
        } else {
            const collectionNames = collections.map((c, i) => `${i + 1}. ${c.name}`).join("\n");
            const selection = prompt(`Save "${businessName}" to which collection?\n\n${collectionNames}\n\nEnter the number (or press Enter for "${collections[0].name}"):`);

            if (selection === null) return; // User cancelled

            let targetCollection;
            if (selection === "" || selection === "1") {
                targetCollection = collections[0];
            } else {
                const index = parseInt(selection) - 1;
                if (index >= 0 && index < collections.length) {
                    targetCollection = collections[index];
                } else {
                    alert("Invalid selection");
                    return;
                }
            }

            const result = await saveBusiness(userId, businessId, targetCollection.collectionId);
            if (result.status === "success") {
                saveBtn.classList.add("saved");
                saveBtn.textContent = "★ Saved";
                saveBtn.title = "Saved";
            } else {
                alert("Failed to save: " + result.message);
            }
        }
    } catch (error) {
        console.error("Error saving business:", error);
        alert("An error occurred while saving the business.");
    }
}

async function handleUnsaveMap(businessId, businessName, saveBtn) {
    try {
        const result = await unsaveBusiness(userId, businessId);
        if (result.status === "success") {
            saveBtn.classList.remove("saved");
            saveBtn.textContent = "☆ Save";
            saveBtn.title = "Save to collection";
        } else {
            alert("Failed to unsave: " + result.message);
        }
    } catch (error) {
        console.error("Error unsaving business:", error);
        alert("An error occurred while removing the business.");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    setupEventListeners();
    setupModalListeners();
    loadBusinesses();
});
