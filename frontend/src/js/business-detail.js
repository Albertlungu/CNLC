import {
    requireAuth,
    logout,
    getSession,
    getBusinessById,
    getReviewsForBusiness,
    createReview,
    deleteReview,
    addReplyToReview,
    deleteReply,
    voteHelpful,
    checkUserReview,
    uploadReviewPhoto,
    checkBusinessSaved,
    saveBusiness,
    unsaveBusiness,
    getUserCollections,
    createCollection,
} from "./api-client.js";
import { initNotifications } from "./notifications.js";

if (!requireAuth()) {
    throw new Error("Authentication required");
}
initNotifications();

const businessInfoEl = document.getElementById("business-info");
const ratingSummaryEl = document.getElementById("rating-summary");
const reviewFormContainer = document.getElementById("review-form-container");
const alreadyReviewedEl = document.getElementById("already-reviewed");
const reviewsListEl = document.getElementById("reviews-list");
const reviewForm = document.getElementById("review-form");
const starSelector = document.getElementById("star-selector");
const ratingInput = document.getElementById("rating-input");
const reviewTextEl = document.getElementById("review-text");
const charCountEl = document.getElementById("char-count");
const photoInput = document.getElementById("photo-input");
const photoPreviewEl = document.getElementById("photo-preview");
const logoutBtn = document.getElementById("logout-btn");

let currentBusinessId = null;
let currentUser = null;
let selectedRating = 0;
let uploadedPhotos = [];

async function getUserProfile(username) {
    const response = await fetch(`http://127.0.0.1:5001/api/auth/profile?username=${username}`);
    return await response.json();
}

function getBusinessIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get("id");
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

function renderStars(rating, maxStars = 5) {
    let stars = "";
    for (let i = 1; i <= maxStars; i++) {
        stars += i <= rating ? "*" : "-";
    }
    return stars;
}

function renderStarsHTML(rating, maxStars = 5) {
    let html = "";
    for (let i = 1; i <= maxStars; i++) {
        html += `<span class="star ${i <= rating ? "" : "empty"}">*</span>`;
    }
    return html;
}

function formatDate(isoString) {
    if (!isoString) return "";
    const date = new Date(isoString);
    return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
    });
}

async function loadBusinessInfo() {
    const businessId = getBusinessIdFromUrl();
    if (!businessId) {
        businessInfoEl.innerHTML = '<div class="error-message">No business ID provided.</div>';
        return;
    }

    currentBusinessId = parseInt(businessId, 10);

    try {
        const result = await getBusinessById(currentBusinessId);

        if (!result.business) {
            businessInfoEl.innerHTML = '<div class="error-message">Business not found.</div>';
            return;
        }

        const business = result.business;
        const addressText = formatAddress(business.address);
        const categoryText = business.category || "Uncategorized";

        // Check if business is saved
        let isSaved = false;
        try {
            const session = getSession();
            const userId = session.userId;
            const savedResult = await checkBusinessSaved(userId, currentBusinessId);
            isSaved = savedResult.saved;
        } catch (error) {
            console.error("Error checking saved status:", error);
        }

        businessInfoEl.innerHTML = `
            <div class="business-header">
                <div class="business-title-section">
                    <h1>${business.name}</h1>
                    <button id="save-business-btn" class="save-business-btn ${isSaved ? 'saved' : ''}" title="${isSaved ? 'Saved' : 'Save to collection'}">
                        ${isSaved ? '★' : '☆'} ${isSaved ? 'Saved' : 'Save'}
                    </button>
                </div>
                <div class="business-meta">
                    <span class="category-badge">${categoryText}</span>
                    <span>${addressText}</span>
                </div>
                ${business.description ? `<p class="business-description">${business.description}</p>` : ""}
            </div>
        `;

        // Add save button listener
        const saveBtn = document.getElementById("save-business-btn");
        if (saveBtn) {
            saveBtn.addEventListener("click", async () => {
                const session = getSession();
                const userId = session.userId;

                if (saveBtn.classList.contains("saved")) {
                    await handleUnsaveBusinessDetail(userId, currentBusinessId, business.name, saveBtn);
                } else {
                    await handleSaveBusinessDetail(userId, currentBusinessId, business.name, saveBtn);
                }
            });
        }

        // Show 3D model viewer for demo business (first business or specific ID)
        // To enable for a specific business, set DEMO_3D_BUSINESS_ID to that business's ID
        const DEMO_3D_BUSINESS_ID = null; // Set to a specific business ID, or null to show for all
        const modelSection = document.getElementById("model-viewer-section");
        if (modelSection) {
            if (DEMO_3D_BUSINESS_ID === null || currentBusinessId === DEMO_3D_BUSINESS_ID) {
                modelSection.style.display = "block";
            }
        }
    } catch (error) {
        console.error("Error loading business:", error);
        businessInfoEl.innerHTML = '<div class="error-message">Failed to load business details.</div>';
    }
}

async function loadReviews() {
    if (!currentBusinessId) return;

    try {
        const result = await getReviewsForBusiness(currentBusinessId);

        if (result.status !== "success") {
            reviewsListEl.innerHTML = '<div class="error-message">Failed to load reviews.</div>';
            return;
        }

        const avgRating = result.averageRating;
        const reviewCount = result.count;

        if (avgRating !== null) {
            ratingSummaryEl.innerHTML = `
                <span class="avg-rating">${avgRating.toFixed(1)}</span>
                <span class="star-display">${renderStars(Math.round(avgRating))}</span>
                <span class="review-count">(${reviewCount} review${reviewCount !== 1 ? "s" : ""})</span>
            `;
        } else {
            ratingSummaryEl.innerHTML = `
                <span class="avg-rating">--</span>
                <span class="star-display">-----</span>
                <span class="review-count">(0 reviews)</span>
            `;
        }

        if (result.reviews.length === 0) {
            reviewsListEl.innerHTML = '<div class="no-reviews">No reviews yet. Be the first to review!</div>';
            return;
        }

        reviewsListEl.innerHTML = result.reviews.map(review => renderReviewCard(review)).join("");
        attachReviewEventListeners();

    } catch (error) {
        console.error("Error loading reviews:", error);
        reviewsListEl.innerHTML = '<div class="error-message">Failed to load reviews.</div>';
    }
}

function renderReviewCard(review) {
    const isOwner = currentUser && currentUser.username === review.username;
    const photosHtml = review.photos && review.photos.length > 0
        ? `<div class="review-photos">${review.photos.map(p => `<img src="${p}" alt="Review photo">`).join("")}</div>`
        : "";

    const repliesHtml = review.replies && review.replies.length > 0
        ? `<div class="replies-section">${review.replies.map(reply => renderReplyCard(reply, review.reviewId)).join("")}</div>`
        : "";

    return `
        <div class="review-card" data-review-id="${review.reviewId}">
            <div class="review-header">
                <div class="reviewer-info">
                    <span class="reviewer-name">${review.username}</span>
                    <span class="review-date">${formatDate(review.createdAt)}</span>
                </div>
                <div class="review-rating">
                    ${renderStarsHTML(review.rating)}
                </div>
            </div>
            <p class="review-content">${review.review}</p>
            ${photosHtml}
            <div class="review-actions">
                <button class="helpful-btn" data-review-id="${review.reviewId}">
                    Helpful (<span class="helpful-count">${review.helpful || 0}</span>)
                </button>
                <button class="reply-btn" data-review-id="${review.reviewId}">Reply</button>
                ${isOwner ? `<button class="delete-btn" data-review-id="${review.reviewId}">Delete</button>` : ""}
            </div>
            <div class="reply-form" id="reply-form-${review.reviewId}">
                <textarea placeholder="Write a reply..." maxlength="500"></textarea>
                <div class="reply-form-actions">
                    <button class="reply-submit-btn" data-review-id="${review.reviewId}">Submit Reply</button>
                    <button class="reply-cancel-btn" data-review-id="${review.reviewId}">Cancel</button>
                </div>
            </div>
            ${repliesHtml}
        </div>
    `;
}

function renderReplyCard(reply, reviewId) {
    const isOwner = currentUser && currentUser.username === reply.username;
    return `
        <div class="reply-card" data-reply-id="${reply.replyId}">
            <div class="reply-header">
                <span class="reply-author">${reply.username}</span>
                <span class="reply-date">${formatDate(reply.createdAt)}</span>
            </div>
            <p class="reply-content">${reply.content}</p>
            ${isOwner ? `<button class="delete-btn delete-reply-btn" data-review-id="${reviewId}" data-reply-id="${reply.replyId}">Delete</button>` : ""}
        </div>
    `;
}

function attachReviewEventListeners() {
    document.querySelectorAll(".helpful-btn").forEach(btn => {
        btn.addEventListener("click", handleHelpfulVote);
    });

    document.querySelectorAll(".reply-btn").forEach(btn => {
        btn.addEventListener("click", toggleReplyForm);
    });

    document.querySelectorAll(".reply-submit-btn").forEach(btn => {
        btn.addEventListener("click", handleReplySubmit);
    });

    document.querySelectorAll(".reply-cancel-btn").forEach(btn => {
        btn.addEventListener("click", toggleReplyForm);
    });

    document.querySelectorAll(".delete-btn:not(.delete-reply-btn)").forEach(btn => {
        btn.addEventListener("click", handleDeleteReview);
    });

    document.querySelectorAll(".delete-reply-btn").forEach(btn => {
        btn.addEventListener("click", handleDeleteReply);
    });
}

async function handleHelpfulVote(e) {
    const reviewId = parseInt(e.target.dataset.reviewId, 10);
    try {
        const result = await voteHelpful(reviewId);
        if (result.status === "success") {
            e.target.querySelector(".helpful-count").textContent = result.helpful;
        }
    } catch (error) {
        console.error("Error voting helpful:", error);
    }
}

function toggleReplyForm(e) {
    const reviewId = e.target.dataset.reviewId;
    const replyForm = document.getElementById(`reply-form-${reviewId}`);
    replyForm.classList.toggle("active");
}

async function handleReplySubmit(e) {
    const reviewId = parseInt(e.target.dataset.reviewId, 10);
    const replyForm = document.getElementById(`reply-form-${reviewId}`);
    const textarea = replyForm.querySelector("textarea");
    const content = textarea.value.trim();

    if (!content) {
        alert("Please enter a reply.");
        return;
    }

    try {
        const result = await addReplyToReview(reviewId, currentUser.id, currentUser.username, content);
        if (result.status === "success") {
            textarea.value = "";
            replyForm.classList.remove("active");
            loadReviews();
        } else {
            alert("Failed to add reply: " + result.message);
        }
    } catch (error) {
        console.error("Error adding reply:", error);
        alert("Failed to add reply.");
    }
}

async function handleDeleteReview(e) {
    const reviewId = parseInt(e.target.dataset.reviewId, 10);
    if (!confirm("Are you sure you want to delete this review?")) return;

    try {
        const result = await deleteReview(reviewId, currentUser.username);
        if (result.status === "success") {
            loadReviews();
            checkUserCanReview();
        } else {
            alert("Failed to delete review: " + result.message);
        }
    } catch (error) {
        console.error("Error deleting review:", error);
        alert("Failed to delete review.");
    }
}

async function handleDeleteReply(e) {
    const reviewId = parseInt(e.target.dataset.reviewId, 10);
    const replyId = parseInt(e.target.dataset.replyId, 10);
    if (!confirm("Are you sure you want to delete this reply?")) return;

    try {
        const result = await deleteReply(reviewId, replyId, currentUser.username);
        if (result.status === "success") {
            loadReviews();
        } else {
            alert("Failed to delete reply: " + result.message);
        }
    } catch (error) {
        console.error("Error deleting reply:", error);
        alert("Failed to delete reply.");
    }
}

async function checkUserCanReview() {
    if (!currentUser || !currentBusinessId) return;

    try {
        const result = await checkUserReview(currentBusinessId, currentUser.id);
        if (result.hasReviewed) {
            reviewFormContainer.style.display = "none";
            alreadyReviewedEl.style.display = "block";
        } else {
            reviewFormContainer.style.display = "block";
            alreadyReviewedEl.style.display = "none";
        }
    } catch (error) {
        console.error("Error checking user review:", error);
    }
}

function setupStarRating() {
    const stars = starSelector.querySelectorAll(".star");

    stars.forEach(star => {
        star.addEventListener("mouseenter", () => {
            const rating = parseInt(star.dataset.rating, 10);
            updateStarDisplay(rating, true);
        });

        star.addEventListener("mouseleave", () => {
            updateStarDisplay(selectedRating, false);
        });

        star.addEventListener("click", () => {
            selectedRating = parseInt(star.dataset.rating, 10);
            ratingInput.value = selectedRating;
            updateStarDisplay(selectedRating, false);
        });
    });
}

function updateStarDisplay(rating, isHover) {
    const stars = starSelector.querySelectorAll(".star");
    stars.forEach(star => {
        const starRating = parseInt(star.dataset.rating, 10);
        star.classList.remove("active", "hovered");
        if (starRating <= rating) {
            star.classList.add(isHover ? "hovered" : "active");
        }
    });
}

function setupCharCounter() {
    reviewTextEl.addEventListener("input", () => {
        charCountEl.textContent = reviewTextEl.value.length;
    });
}

function setupPhotoUpload() {
    photoInput.addEventListener("change", async (e) => {
        const files = Array.from(e.target.files);
        photoPreviewEl.innerHTML = "";
        uploadedPhotos = [];

        for (const file of files) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const img = document.createElement("img");
                img.src = e.target.result;
                photoPreviewEl.appendChild(img);
            };
            reader.readAsDataURL(file);

            try {
                const result = await uploadReviewPhoto(file);
                if (result.status === "success") {
                    uploadedPhotos.push(result.photoUrl);
                }
            } catch (error) {
                console.error("Error uploading photo:", error);
            }
        }
    });
}

async function handleReviewSubmit(e) {
    e.preventDefault();

    if (selectedRating === 0) {
        alert("Please select a rating.");
        return;
    }

    const reviewText = reviewTextEl.value.trim();
    if (!reviewText) {
        alert("Please write a review.");
        return;
    }

    try {
        const result = await createReview(
            currentBusinessId,
            currentUser.id,
            currentUser.username,
            selectedRating,
            reviewText,
            uploadedPhotos
        );

        if (result.status === "success") {
            reviewTextEl.value = "";
            charCountEl.textContent = "0";
            selectedRating = 0;
            ratingInput.value = "0";
            updateStarDisplay(0, false);
            photoInput.value = "";
            photoPreviewEl.innerHTML = "";
            uploadedPhotos = [];

            loadReviews();
            checkUserCanReview();
        } else {
            alert("Failed to submit review: " + result.message);
        }
    } catch (error) {
        console.error("Error submitting review:", error);
        alert("Failed to submit review.");
    }
}

// Modal Functions
let selectedCollectionId = null;
let pendingSaveBusinessId = null;
let pendingSaveBtn = null;

function openCollectionModal(businessId, businessName, collections, saveBtn) {
    const collectionModal = document.getElementById("collection-modal");
    const modalBusinessName = document.getElementById("modal-business-name");
    const collectionList = document.getElementById("collection-list");

    pendingSaveBusinessId = businessId;
    pendingSaveBtn = saveBtn;
    selectedCollectionId = collections[0].collectionId;

    modalBusinessName.textContent = `Save "${businessName}" to:`;

    collectionList.innerHTML = collections.map(c => `
        <div class="collection-option ${c.collectionId === selectedCollectionId ? 'selected' : ''}" data-collection-id="${c.collectionId}">
            ${c.name}
        </div>
    `).join('');

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
    const collectionModal = document.getElementById("collection-modal");
    collectionModal.classList.remove('active');
    selectedCollectionId = null;
    pendingSaveBusinessId = null;
    pendingSaveBtn = null;
}

async function confirmSaveToCollection(userId) {
    if (!selectedCollectionId || !pendingSaveBusinessId || !pendingSaveBtn) return;

    try {
        const result = await saveBusiness(userId, pendingSaveBusinessId, selectedCollectionId);
        if (result.status === "success") {
            pendingSaveBtn.classList.add("saved");
            pendingSaveBtn.textContent = "★ Saved";
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

// Save/Unsave Business Handlers
async function handleSaveBusinessDetail(userId, businessId, businessName, saveBtn) {
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
            openCollectionModal(businessId, businessName, collections, saveBtn);
        }
    } catch (error) {
        console.error("Error saving business:", error);
        alert("An error occurred while saving the business.");
    }
}

async function handleUnsaveBusinessDetail(userId, businessId, businessName, saveBtn) {
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

function setupModalListeners(userId) {
    const collectionModal = document.getElementById("collection-modal");
    const modalCancelBtn = document.getElementById("modal-cancel-btn");
    const modalConfirmBtn = document.getElementById("modal-confirm-btn");
    const modalClose = document.querySelector(".modal-close");

    modalCancelBtn.addEventListener('click', closeCollectionModal);
    modalClose.addEventListener('click', closeCollectionModal);
    modalConfirmBtn.addEventListener('click', () => confirmSaveToCollection(userId));

    collectionModal.addEventListener('click', (e) => {
        if (e.target === collectionModal) {
            closeCollectionModal();
        }
    });
}

async function init() {
    const session = getSession();
    if (!session) {
        window.location.href = "auth.html";
        return;
    }

    try {
        const profileResult = await getUserProfile(session.username);
        if (profileResult.status === "success") {
            currentUser = profileResult.user;
        }
    } catch (error) {
        console.error("Error loading user profile:", error);
    }

    await loadBusinessInfo();
    await loadReviews();
    await checkUserCanReview();

    setupStarRating();
    setupCharCounter();
    setupModalListeners(session.userId);
    setupPhotoUpload();

    reviewForm.addEventListener("submit", handleReviewSubmit);

    if (logoutBtn) {
        logoutBtn.addEventListener("click", (e) => {
            e.preventDefault();
            logout();
        });
    }
}

document.addEventListener("DOMContentLoaded", init);
