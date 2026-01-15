import { filterBusinesses } from "./api-client.js";
import { getUserLocation } from "./utils/helper.js";

const filterState = {
    hours: {
        rangeStart: 0,
        rangeEnd: 24,
    },
    categories: [],
    ratings: [],
    radius: null,
};

const grid = document.getElementById("business-grid");
const prevPageBtn = document.getElementById("prev-page");
const nextPageBtn = document.getElementById("next-page");

let currentPage = 1;
const businessesPerPage = 30;
// const totalBusinesses = 1000;



function createBusinessCard(business) {
    const box = document.createElement("div");
    box.className = "business-box";

    box.innerHTML = `
    <div class="dropdown-bar">
      ${business.name}
      <span class="arrow">&#9662;</span>
    </div>
    <div class="description">
        ${business.address}, ${business.city}
    </div>
  `;

    const bar = box.querySelector(".dropdown-bar");
    const arrow = bar.querySelector(".arrow");
    const desc = box.querySelector(".description");
    bar.addEventListener("click", () => {
        desc.classList.toggle("show");
        arrow.classList.toggle("rotate");
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

    console.log("Calling API with:", { category: filterState.categories[0], lat, lon, radius: filterState.radius, page });

    try {
        const offset = (page - 1) * businessesPerPage;
        const result = await filterBusinesses(
            filterState.categories[0],
            lat,
            lon,
            filterState.radius,
            offset,
            businessesPerPage
        );
        console.log("API Response:", result);
        console.log("Number of businesses:", result.businesses?.length);

        if (result.status === 'success') {
            grid.innerHTML = "";

            result.businesses.forEach(business => {
                const card = createBusinessCard(business);
                console.log("Created card for:", business.name);
                grid.appendChild(card);
            });

            console.log("Grid children count:", grid.children.length);
            grid.style.opacity = 1;
        } else {
            console.error("API did not return success status");
        }
    } catch (e) {
        console.error("Error rendering businesses: ", e);
    }
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

function updateButtons() {
    prevPageBtn.disabled = currentPage === 1;
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
    logFilterState();

    renderPage(currentPage);

    prevPageBtn.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            renderPage(currentPage);
        }
    });

    nextPageBtn.addEventListener("click", () => {
        currentPage++;
        renderPage(currentPage);
    });
});

function initializeFilters() {
    updateHourRangeText();
}

function setupEventListeners() {
    const filterHeaders = document.querySelectorAll(".filter-header");
    filterHeaders.forEach((header) => {
        header.addEventListener("click", function () {
            toggleFilter(this);
        });
    });

    const hourSliders = document.querySelectorAll(
        '.hours-slider input[type="range"]',
    );
    hourSliders.forEach((slider, index) => {
        slider.addEventListener("input", function (e) {
            if (index === 0) {
                filterState.hours.rangeStart = parseInt(e.target.value);
            } else {
                filterState.hours.rangeEnd = parseInt(e.target.value);
            }
            updateHourRangeText();
            logFilterState();
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
            logFilterState();
            renderPage(currentPage);
        });
    });

    const radiusRadios = document.querySelectorAll('input[name="radius"]');
    radiusRadios.forEach((radio) => {
        radio.addEventListener("change", function (e) {
            if (e.target.checked) {
                filterState.radius = e.target.value;
                console.log("Radius changed:", filterState.radius);
                logFilterState();
                renderPage(currentPage);
            }
        });
    });
}

function updateHourRangeText() {
    const hourRangeText = document.getElementById("hour-range-text");
    if (hourRangeText) {
        const startHour = filterState.hours.rangeStart;
        const endHour = filterState.hours.rangeEnd;
        hourRangeText.textContent = `${formatHour(startHour)} - ${formatHour(endHour)}`;
    }
}

function formatHour(hour) {
    return `${hour.toString().padStart(2, "0")}:00`;
}

function logFilterState() {
    console.log("=== Current Filter State ===");
    console.log("Hours:", filterState.hours);
    console.log("Categories:", filterState.categories);
    console.log("Ratings:", filterState.ratings);
    console.log("Radius:", filterState.radius);
    console.log("==========================");
}

function getFilterState() {
    return JSON.parse(JSON.stringify(filterState));
}

function resetFilters() {
    filterState.hours = {
        rangeStart: 0,
        rangeEnd: 24,
    };
    const hourSliders = document.querySelectorAll(
        '.hours-slider input[type="range"]',
    );
    hourSliders[0].value = 0;
    hourSliders[1].value = 24;
    updateHourRangeText();

    filterState.categories = [];
    document
        .querySelectorAll(".category")
        .forEach((cb) => (cb.checked = false));

    filterState.ratings = [];
    document.querySelectorAll(".rating").forEach((cb) => (cb.checked = false));

    filterState.radius = null;
    document
        .querySelectorAll('input[name="radius"]')
        .forEach((radio) => (radio.checked = false));

    console.log("Filters reset to default state");
    logFilterState();
}

function applyFilters() {
    console.log("Applying filters with state:", getFilterState());
}

if (typeof module !== "undefined" && module.exports) {
    module.exports = {
        getFilterState,
        resetFilters,
        applyFilters,
    };
}
