import {
    requireAuth,
    logout,
    getSession,
    isBusinessOwner,
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
    getBlogPosts,
    createBlogPost,
    deleteBlogPost,
    uploadBlogImage,
    getBusinessMedia,
    uploadBusinessMedia,
    deleteBusinessMedia,
    uploadVideoScan,
    getScanStatus,
    listScans,
} from "./api-client.js";
import { initNotifications } from "./notifications.js";
import { initNavbar } from "./components/navbar.js";

if (!requireAuth()) {
    throw new Error("Authentication required");
}
initNotifications();
initNavbar("directory");

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

// ==================== Media Section ====================

async function loadMedia() {
    if (!currentBusinessId) return;
    try {
        const result = await getBusinessMedia(currentBusinessId);
        const media = result.media || [];
        const section = document.getElementById("media-section");
        const container = document.getElementById("media-container");

        if (media.length === 0 && !isBusinessOwner(parseInt(currentBusinessId))) return;

        section.style.display = "block";
        container.innerHTML = "";

        for (const m of media) {
            const el = document.createElement("div");
            el.className = "media-item";

            if (m.mediaType === "3d") {
                el.innerHTML = `
                    <model-viewer src="${m.url}" alt="${m.originalName}" auto-rotate camera-controls
                        shadow-intensity="1" style="width:100%;height:400px;border-radius:12px;background:#f5f5f5;">
                    </model-viewer>
                    <div class="media-item-label">${m.originalName}</div>
                `;
            } else {
                el.innerHTML = `
                    <video controls playsinline style="width:100%;border-radius:12px;">
                        <source src="${m.url}" type="${m.mimeType}">
                    </video>
                    <div class="media-item-label">${m.originalName}</div>
                `;
            }

            if (isBusinessOwner(parseInt(currentBusinessId))) {
                const deleteBtn = document.createElement("button");
                deleteBtn.className = "media-delete-btn";
                deleteBtn.textContent = "Delete";
                deleteBtn.addEventListener("click", async () => {
                    if (!confirm("Delete this media?")) return;
                    const session = getSession();
                    await deleteBusinessMedia(m.mediaId, session.userId);
                    await loadMedia();
                });
                el.appendChild(deleteBtn);
            }

            container.appendChild(el);
        }
    } catch (err) {
        console.error("Error loading media:", err);
    }
}

function setupMediaUpload() {
    const btn = document.getElementById("upload-media-btn");
    const modal = document.getElementById("upload-media-modal");
    const closeBtn = document.getElementById("media-modal-close");
    const cancelBtn = document.getElementById("media-upload-cancel");
    const submitBtn = document.getElementById("media-upload-submit");
    const dropZone = document.getElementById("media-drop-zone");
    const fileInput = document.getElementById("media-file-input");
    const preview = document.getElementById("media-upload-preview");
    const filenameEl = document.getElementById("media-upload-filename");

    if (!btn) return;

    let selectedFile = null;

    btn.addEventListener("click", () => { modal.style.display = "flex"; });
    closeBtn.addEventListener("click", () => { modal.style.display = "none"; selectedFile = null; });
    cancelBtn.addEventListener("click", () => { modal.style.display = "none"; selectedFile = null; });

    dropZone.addEventListener("click", () => fileInput.click());
    dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("drag-over"); });
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("drag-over");
        if (e.dataTransfer.files.length) { selectedFile = e.dataTransfer.files[0]; showFilePreview(); }
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length) { selectedFile = fileInput.files[0]; showFilePreview(); }
    });

    function showFilePreview() {
        if (!selectedFile) return;
        filenameEl.textContent = selectedFile.name;
        preview.style.display = "block";
        submitBtn.disabled = false;
    }

    submitBtn.addEventListener("click", async () => {
        if (!selectedFile) return;
        submitBtn.disabled = true;
        submitBtn.textContent = "Uploading...";
        const session = getSession();
        try {
            await uploadBusinessMedia(parseInt(currentBusinessId), session.userId, selectedFile);
            modal.style.display = "none";
            selectedFile = null;
            preview.style.display = "none";
            await loadMedia();
        } catch (err) {
            alert("Upload failed: " + (err.message || err));
        }
        submitBtn.disabled = false;
        submitBtn.textContent = "Upload";
    });
}

// ==================== Blog Section ====================

async function loadBlogPosts() {
    if (!currentBusinessId) return;
    try {
        const result = await getBlogPosts(parseInt(currentBusinessId));
        const posts = result.posts || [];
        const section = document.getElementById("blog-section");
        const container = document.getElementById("blog-posts");

        if (posts.length === 0 && !isBusinessOwner(parseInt(currentBusinessId))) return;

        section.style.display = "block";
        container.innerHTML = "";

        if (posts.length === 0) {
            container.innerHTML = '<p class="blog-empty">No blog posts yet.</p>';
            return;
        }

        for (const post of posts) {
            const el = document.createElement("article");
            el.className = "blog-post-card";

            const date = new Date(post.createdAt).toLocaleDateString("en-CA", {
                year: "numeric", month: "long", day: "numeric"
            });

            let coverHtml = "";
            if (post.coverImage) {
                coverHtml = `<img src="${post.coverImage}" alt="" class="blog-cover-image">`;
            }

            let tagsHtml = "";
            if (post.tags && post.tags.length) {
                tagsHtml = `<div class="blog-tags">${post.tags.map(t => `<span class="blog-tag">${t}</span>`).join("")}</div>`;
            }

            let deleteHtml = "";
            if (isBusinessOwner(parseInt(currentBusinessId))) {
                deleteHtml = `<button class="blog-delete-btn" data-post-id="${post.postId}">Delete</button>`;
            }

            // Simple markdown: bold, italic, headers, line breaks
            let contentHtml = post.content
                .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
                .replace(/^### (.+)$/gm, "<h4>$1</h4>")
                .replace(/^## (.+)$/gm, "<h3>$1</h3>")
                .replace(/^# (.+)$/gm, "<h2>$1</h2>")
                .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
                .replace(/\*(.+?)\*/g, "<em>$1</em>")
                .replace(/\n/g, "<br>");

            el.innerHTML = `
                ${coverHtml}
                <div class="blog-post-body">
                    <h3 class="blog-post-title">${post.title}</h3>
                    <div class="blog-post-meta">${date}</div>
                    ${tagsHtml}
                    <div class="blog-post-content">${contentHtml}</div>
                    ${deleteHtml}
                </div>
            `;

            container.appendChild(el);
        }

        // Wire up delete buttons
        container.querySelectorAll(".blog-delete-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                if (!confirm("Delete this post?")) return;
                const session = getSession();
                await deleteBlogPost(parseInt(btn.dataset.postId), session.userId);
                await loadBlogPosts();
            });
        });
    } catch (err) {
        console.error("Error loading blog posts:", err);
    }
}

function setupBlogPostModal() {
    const btn = document.getElementById("write-post-btn");
    const modal = document.getElementById("blog-post-modal");
    const closeBtn = document.getElementById("blog-modal-close");
    const cancelBtn = document.getElementById("blog-post-cancel");
    const submitBtn = document.getElementById("blog-post-submit");

    if (!btn) return;

    btn.addEventListener("click", () => { modal.style.display = "flex"; });
    closeBtn.addEventListener("click", () => { modal.style.display = "none"; });
    cancelBtn.addEventListener("click", () => { modal.style.display = "none"; });

    submitBtn.addEventListener("click", async () => {
        const title = document.getElementById("blog-title").value.trim();
        const content = document.getElementById("blog-content").value.trim();
        const tagsRaw = document.getElementById("blog-tags").value.trim();
        const tags = tagsRaw ? tagsRaw.split(",").map(t => t.trim()).filter(Boolean) : [];
        const coverInput = document.getElementById("blog-cover-image");

        if (!title || !content) {
            alert("Title and content are required.");
            return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = "Publishing...";

        let coverImage = null;
        if (coverInput.files.length) {
            try {
                const uploadResult = await uploadBlogImage(coverInput.files[0]);
                if (uploadResult.status === "success") {
                    coverImage = uploadResult.imageUrl;
                }
            } catch (err) {
                console.error("Cover image upload failed:", err);
            }
        }

        const session = getSession();
        try {
            await createBlogPost(session.userId, parseInt(currentBusinessId), title, content, tags, coverImage);
            modal.style.display = "none";
            document.getElementById("blog-title").value = "";
            document.getElementById("blog-content").value = "";
            document.getElementById("blog-tags").value = "";
            coverInput.value = "";
            await loadBlogPosts();
        } catch (err) {
            alert("Failed to publish: " + (err.message || err));
        }

        submitBtn.disabled = false;
        submitBtn.textContent = "Publish";
    });
}

// ==================== 3D Scan Section ====================

async function loadScans() {
    if (!currentBusinessId) return;
    try {
        const result = await listScans(currentBusinessId);
        const scans = result.scans || [];
        const section = document.getElementById("scan-section");
        const container = document.getElementById("scan-container");

        if (scans.length === 0 && !isBusinessOwner(parseInt(currentBusinessId))) {
            container.innerHTML = '<p class="scan-empty">No 3D scans available for this business yet.</p>';
            return;
        }

        container.innerHTML = "";

        if (scans.length === 0) {
            container.innerHTML = '<p class="scan-empty">No 3D scans yet. Upload a video to generate one.</p>';
            return;
        }

        for (const scan of scans) {
            const el = document.createElement("div");
            el.className = "scan-item";

            if (scan.status === "completed" && scan.outputPath) {
                el.innerHTML = `
                    <model-viewer src="http://127.0.0.1:5001${scan.outputPath}" alt="3D Scan"
                        auto-rotate camera-controls ar
                        shadow-intensity="1" style="width:100%;height:400px;border-radius:12px;background:#f5f5f5;">
                    </model-viewer>
                    <div class="scan-item-label">3D Scan - ${new Date(scan.createdAt).toLocaleDateString()}</div>
                `;
            } else if (scan.status === "processing") {
                el.innerHTML = `
                    <div class="scan-processing">
                        <div class="scan-spinner"></div>
                        <p>Processing 3D scan...</p>
                        <p class="scan-step">${scan.currentStep || "Queued"}</p>
                    </div>
                `;
                el.dataset.scanId = scan.scanId;
                el.classList.add("scan-polling");
            } else if (scan.status === "failed") {
                el.innerHTML = `
                    <div class="scan-failed">
                        <p>Scan processing failed</p>
                        <p class="scan-error">${scan.error || "Unknown error"}</p>
                    </div>
                `;
            } else {
                el.innerHTML = `
                    <div class="scan-processing">
                        <div class="scan-spinner"></div>
                        <p>Scan queued for processing...</p>
                    </div>
                `;
                el.dataset.scanId = scan.scanId;
                el.classList.add("scan-polling");
            }

            container.appendChild(el);
        }

        // Start polling for in-progress scans
        startScanPolling();
    } catch (err) {
        console.error("Error loading scans:", err);
    }
}

let scanPollInterval = null;

function startScanPolling() {
    if (scanPollInterval) clearInterval(scanPollInterval);

    const pollingItems = document.querySelectorAll(".scan-polling");
    if (pollingItems.length === 0) return;

    scanPollInterval = setInterval(async () => {
        const items = document.querySelectorAll(".scan-polling");
        if (items.length === 0) {
            clearInterval(scanPollInterval);
            scanPollInterval = null;
            return;
        }

        for (const item of items) {
            const scanId = item.dataset.scanId;
            if (!scanId) continue;
            try {
                const result = await getScanStatus(scanId);
                if (result.status === "success") {
                    const scan = result.scan;
                    if (scan.status === "completed" || scan.status === "failed") {
                        // Reload all scans to show updated state
                        clearInterval(scanPollInterval);
                        scanPollInterval = null;
                        await loadScans();
                        return;
                    }
                    // Update step text
                    const stepEl = item.querySelector(".scan-step");
                    if (stepEl && scan.currentStep) {
                        stepEl.textContent = scan.currentStep;
                    }
                }
            } catch (err) {
                console.error("Error polling scan status:", err);
            }
        }
    }, 5000); // Poll every 5 seconds
}

function setupScanUpload() {
    const btn = document.getElementById("upload-scan-btn");
    const modal = document.getElementById("scan-upload-modal");
    const closeBtn = document.getElementById("scan-modal-close");
    const cancelBtn = document.getElementById("scan-upload-cancel");
    const submitBtn = document.getElementById("scan-upload-submit");
    const dropZone = document.getElementById("scan-drop-zone");
    const fileInput = document.getElementById("scan-file-input");
    const preview = document.getElementById("scan-upload-preview");
    const filenameEl = document.getElementById("scan-upload-filename");
    const filesizeEl = document.getElementById("scan-upload-filesize");
    const progressEl = document.getElementById("scan-upload-progress");
    const progressText = document.getElementById("scan-progress-text");

    if (!btn) return;

    let selectedFile = null;

    btn.addEventListener("click", () => { modal.style.display = "flex"; });
    closeBtn.addEventListener("click", () => { resetScanModal(); });
    cancelBtn.addEventListener("click", () => { resetScanModal(); });

    modal.addEventListener("click", (e) => {
        if (e.target === modal) resetScanModal();
    });

    function resetScanModal() {
        modal.style.display = "none";
        selectedFile = null;
        preview.style.display = "none";
        progressEl.style.display = "none";
        submitBtn.disabled = true;
        submitBtn.textContent = "Upload & Process";
    }

    dropZone.addEventListener("click", () => fileInput.click());
    dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("drag-over"); });
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("drag-over");
        if (e.dataTransfer.files.length) { selectedFile = e.dataTransfer.files[0]; showScanFilePreview(); }
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length) { selectedFile = fileInput.files[0]; showScanFilePreview(); }
    });

    function showScanFilePreview() {
        if (!selectedFile) return;
        filenameEl.textContent = selectedFile.name;
        const sizeMB = (selectedFile.size / (1024 * 1024)).toFixed(1);
        filesizeEl.textContent = `(${sizeMB} MB)`;
        preview.style.display = "block";
        submitBtn.disabled = false;
    }

    submitBtn.addEventListener("click", async () => {
        if (!selectedFile) return;
        submitBtn.disabled = true;
        submitBtn.textContent = "Uploading...";
        progressEl.style.display = "block";
        progressText.textContent = "Uploading video...";

        const session = getSession();
        try {
            const result = await uploadVideoScan(currentBusinessId, session.userId, selectedFile);
            if (result.status === "success") {
                progressText.textContent = "Upload complete! Processing will continue in the background.";
                setTimeout(() => {
                    resetScanModal();
                    loadScans();
                }, 2000);
            } else {
                progressText.textContent = "Upload failed: " + (result.error || "Unknown error");
                submitBtn.disabled = false;
                submitBtn.textContent = "Retry";
            }
        } catch (err) {
            progressText.textContent = "Upload failed: " + (err.message || err);
            submitBtn.disabled = false;
            submitBtn.textContent = "Retry";
        }
    });
}

// ==================== Role-gated UI ====================

function showOwnerControls() {
    if (!currentBusinessId) return;
    const bizId = parseInt(currentBusinessId);
    if (isBusinessOwner(bizId)) {
        const uploadBtn = document.getElementById("upload-media-btn");
        const writeBtn = document.getElementById("write-post-btn");
        const scanBtn = document.getElementById("upload-scan-btn");
        if (uploadBtn) uploadBtn.style.display = "inline-flex";
        if (writeBtn) writeBtn.style.display = "inline-flex";
        if (scanBtn) scanBtn.style.display = "inline-flex";
    }
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

    // Load media, blog, scans, and reviews in parallel
    await Promise.all([loadMedia(), loadBlogPosts(), loadScans(), loadReviews()]);
    await checkUserCanReview();

    showOwnerControls();
    setupStarRating();
    setupCharCounter();
    setupModalListeners(session.userId);
    setupPhotoUpload();
    setupMediaUpload();
    setupScanUpload();
    setupBlogPostModal();

    reviewForm.addEventListener("submit", handleReviewSubmit);
}

document.addEventListener("DOMContentLoaded", init);
