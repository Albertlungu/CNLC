// Auth utilities
export function isLoggedIn() {
    const session = localStorage.getItem("session");
    return session !== null;
}

export function getSession() {
    const session = localStorage.getItem("session");
    return session ? JSON.parse(session) : null;
}

export function requireAuth() {
    if (!isLoggedIn()) {
        window.location.href = "auth.html";
        return false;
    }
    return true;
}

// Logout
export async function logout() {
    const session = getSession();
    if (!session) {
        localStorage.removeItem("session");
        window.location.href = "auth.html";
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:5001/api/auth/logout", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                username: session.username,
            }),
        });
        await response.json();
    } catch (error) {
        console.error("Logout error:", error);
    } finally {
        localStorage.removeItem("session");
        window.location.href = "auth.html";
    }
}

// Login
export async function login(username, password, captchaToken = null) {
    const body = { username, password };
    if (captchaToken) body.recaptchaToken = captchaToken;

    const response = await fetch("http://127.0.0.1:5001/api/auth/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });
    const result = await response.json();
    console.log("Login function has been run.");
    console.log("RESULT: ", result);
    return result;
}

// Register
export async function register(
    username,
    email,
    phone,
    password,
    firstName,
    lastName,
    city,
    country,
    captchaToken = null,
) {
    const body = { username, email, phone, password, firstName, lastName, city, country };
    if (captchaToken) body.recaptchaToken = captchaToken;

    const response = await fetch("http://127.0.0.1:5001/api/auth/register", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });
    const result = await response.json();
    console.log("RESULT: ", result);
    return result;
}


export async function filterBusinesses(search, category, lat1, lon1, radius, minRating, offset = 0, limit = 30) {
    const params = new URLSearchParams();

    if (search) {
        params.append('search', search);
    }
    if (category) {
        params.append('category', category);
    }
    if (lat1 && lon1 && radius) {
        params.append('lat1', lat1);
        params.append('lon1', lon1);
        params.append('radius', radius);
    }
    if (minRating) {
        params.append('min_rating', minRating);
    }
    params.append('offset', offset);
    params.append('limit', limit);

    const url = `http://127.0.0.1:5001/api/businesses?${params.toString()}`;

    try {
        const response = await fetch(url, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            }
        });
        const result = await response.json();
        console.log("RESULT: ", result);
        return result;
    } catch (error) {
        console.error("Error fetching businesses:", error);
        throw error;
    }
}

export async function getBusinessById(businessId) {
    const url = `http://127.0.0.1:5001/api/businesses/${businessId}`;
    const response = await fetch(url);
    return await response.json();
}

export async function getReviewsForBusiness(businessId) {
    const url = `http://127.0.0.1:5001/api/reviews?business_id=${businessId}`;
    const response = await fetch(url);
    return await response.json();
}

export async function createReview(businessId, userId, username, rating, reviewText, photos = []) {
    const response = await fetch("http://127.0.0.1:5001/api/reviews", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            businessID: businessId,
            userID: userId,
            username: username,
            rating: rating,
            review: reviewText,
            photos: photos,
        }),
    });
    return await response.json();
}

export async function updateReview(reviewId, username, rating, reviewText, photos) {
    const body = { username };
    if (rating !== undefined) body.rating = rating;
    if (reviewText !== undefined) body.review = reviewText;
    if (photos !== undefined) body.photos = photos;

    const response = await fetch(`http://127.0.0.1:5001/api/reviews/${reviewId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });
    return await response.json();
}

export async function deleteReview(reviewId, username) {
    const response = await fetch(`http://127.0.0.1:5001/api/reviews/${reviewId}`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ username }),
    });
    return await response.json();
}

export async function addReplyToReview(reviewId, userId, username, content) {
    const response = await fetch(`http://127.0.0.1:5001/api/reviews/${reviewId}/replies`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            userID: userId,
            username: username,
            content: content,
        }),
    });
    return await response.json();
}

export async function deleteReply(reviewId, replyId, username) {
    const response = await fetch(`http://127.0.0.1:5001/api/reviews/${reviewId}/replies/${replyId}`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ username }),
    });
    return await response.json();
}

export async function voteHelpful(reviewId) {
    const response = await fetch(`http://127.0.0.1:5001/api/reviews/${reviewId}/helpful`, {
        method: "POST",
    });
    return await response.json();
}

export async function checkUserReview(businessId, userId) {
    const url = `http://127.0.0.1:5001/api/reviews/check?business_id=${businessId}&user_id=${userId}`;
    const response = await fetch(url);
    return await response.json();
}

export async function uploadReviewPhoto(file) {
    const formData = new FormData();
    formData.append("photo", file);

    const response = await fetch("http://127.0.0.1:5001/api/reviews/upload", {
        method: "POST",
        body: formData,
    });
    return await response.json();
}

// Saved Business / Collections API
export async function getUserCollections(userId) {
    const url = `http://127.0.0.1:5001/api/saved/collections?user_id=${userId}`;
    const response = await fetch(url);
    return await response.json();
}

export async function getCollectionStats(userId) {
    const url = `http://127.0.0.1:5001/api/saved/collections/stats?user_id=${userId}`;
    const response = await fetch(url);
    return await response.json();
}

export async function createCollection(userId, name) {
    const response = await fetch("http://127.0.0.1:5001/api/saved/collections", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            userId: userId,
            name: name,
        }),
    });
    return await response.json();
}

export async function renameCollection(userId, collectionId, newName) {
    const response = await fetch(`http://127.0.0.1:5001/api/saved/collections/${collectionId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            userId: userId,
            name: newName,
        }),
    });
    return await response.json();
}

export async function deleteCollection(userId, collectionId) {
    const response = await fetch(`http://127.0.0.1:5001/api/saved/collections/${collectionId}`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            userId: userId,
        }),
    });
    return await response.json();
}

export async function getSavedBusinesses(userId, collectionId = null) {
    let url = `http://127.0.0.1:5001/api/saved/businesses?user_id=${userId}`;
    if (collectionId) {
        url += `&collection_id=${collectionId}`;
    }
    const response = await fetch(url);
    return await response.json();
}

export async function saveBusiness(userId, businessId, collectionId) {
    const response = await fetch("http://127.0.0.1:5001/api/saved/businesses", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            userId: userId,
            businessId: businessId,
            collectionId: collectionId,
        }),
    });
    return await response.json();
}

export async function unsaveBusiness(userId, businessId, collectionId = null) {
    const body = { userId: userId };
    if (collectionId) {
        body.collectionId = collectionId;
    }

    const response = await fetch(`http://127.0.0.1:5001/api/saved/businesses/${businessId}`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });
    return await response.json();
}

export async function checkBusinessSaved(userId, businessId) {
    const url = `http://127.0.0.1:5001/api/saved/businesses/${businessId}/check?user_id=${userId}`;
    const response = await fetch(url);
    return await response.json();
}

export async function moveBusinessToCollection(userId, businessId, oldCollectionId, newCollectionId) {
    const response = await fetch(`http://127.0.0.1:5001/api/saved/businesses/${businessId}/move`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            userId: userId,
            oldCollectionId: oldCollectionId,
            newCollectionId: newCollectionId,
        }),
    });
    return await response.json();
}

// ==================== Deals API ====================

export async function getDeals(businessId = null, activeOnly = true) {
    const params = new URLSearchParams();
    if (businessId) params.append("business_id", businessId);
    params.append("active_only", activeOnly);
    const response = await fetch(`http://127.0.0.1:5001/api/deals?${params.toString()}`);
    return await response.json();
}

export async function createDeal(businessId, title, description, discountType, discountValue, expiresAt, createdByUserId) {
    const response = await fetch("http://127.0.0.1:5001/api/deals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ businessId, title, description, discountType, discountValue, expiresAt, createdByUserId }),
    });
    return await response.json();
}

export async function deleteDeal(dealId) {
    const response = await fetch(`http://127.0.0.1:5001/api/deals/${dealId}`, { method: "DELETE" });
    return await response.json();
}

export async function saveDeal(userId, dealId) {
    const response = await fetch(`http://127.0.0.1:5001/api/deals/${dealId}/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId }),
    });
    return await response.json();
}

export async function unsaveDeal(userId, dealId) {
    const response = await fetch(`http://127.0.0.1:5001/api/deals/${dealId}/unsave?user_id=${userId}`, { method: "DELETE" });
    return await response.json();
}

export async function scrapeDeals(businessId, businessName, city = "Ottawa") {
    const response = await fetch("http://127.0.0.1:5001/api/deals/scrape", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ businessId, businessName, city }),
    });
    return await response.json();
}

// ==================== Friends API ====================

export async function sendFriendRequest(fromUserId, toUserId) {
    const response = await fetch("http://127.0.0.1:5001/api/friends/request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fromUserId, toUserId }),
    });
    return await response.json();
}

export async function getFriendRequests(userId) {
    const response = await fetch(`http://127.0.0.1:5001/api/friends/requests?user_id=${userId}`);
    return await response.json();
}

export async function acceptFriendRequest(requestId, userId) {
    const response = await fetch(`http://127.0.0.1:5001/api/friends/requests/${requestId}/accept`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId }),
    });
    return await response.json();
}

export async function rejectFriendRequest(requestId, userId) {
    const response = await fetch(`http://127.0.0.1:5001/api/friends/requests/${requestId}/reject`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId }),
    });
    return await response.json();
}

export async function getFriends(userId) {
    const response = await fetch(`http://127.0.0.1:5001/api/friends?user_id=${userId}`);
    return await response.json();
}

export async function removeFriend(friendshipId, userId) {
    const response = await fetch(`http://127.0.0.1:5001/api/friends/${friendshipId}?user_id=${userId}`, { method: "DELETE" });
    return await response.json();
}

export async function getFriendActivity(userId) {
    const response = await fetch(`http://127.0.0.1:5001/api/friends/activity?user_id=${userId}`);
    return await response.json();
}

export async function searchUsers(query, userId) {
    const response = await fetch(`http://127.0.0.1:5001/api/friends/search?q=${encodeURIComponent(query)}&user_id=${userId}`);
    return await response.json();
}

// ==================== Trending API ====================

export async function getTrending(limit = 50) {
    const response = await fetch(`http://127.0.0.1:5001/api/trending?limit=${limit}`);
    return await response.json();
}

export async function uploadReceipt(userId, businessId, amount, receiptImage) {
    const formData = new FormData();
    formData.append("userId", userId);
    formData.append("businessId", businessId);
    formData.append("amount", amount);
    formData.append("receiptImage", receiptImage);

    const response = await fetch("http://127.0.0.1:5001/api/trending/receipts", {
        method: "POST",
        body: formData,
    });
    return await response.json();
}

export async function getBusinessTrendingStats(businessId) {
    const response = await fetch(`http://127.0.0.1:5001/api/trending/${businessId}/stats`);
    return await response.json();
}

export async function getUserReceipts(userId) {
    const response = await fetch(`http://127.0.0.1:5001/api/trending/receipts?user_id=${userId}`);
    return await response.json();
}

// ==================== User Profile API ====================

export async function getUserProfile(username) {
    const response = await fetch(`http://127.0.0.1:5001/api/users/${username}`);
    return await response.json();
}

// ==================== Reservations API ====================

export async function createReservation(userId, businessId, businessName, date, time, partySize, notes = null) {
    const response = await fetch("http://127.0.0.1:5001/api/reservations/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId, businessId, businessName, date, time, partySize, notes }),
    });
    return await response.json();
}

export async function getUserReservations(userId, status = null) {
    let url = `http://127.0.0.1:5001/api/reservations/?user_id=${userId}`;
    if (status) url += `&status=${status}`;
    const response = await fetch(url);
    return await response.json();
}

export async function cancelReservation(reservationId, userId) {
    const response = await fetch(`http://127.0.0.1:5001/api/reservations/${reservationId}/cancel`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId }),
    });
    return await response.json();
}

export async function downloadICS(reservationId) {
    const response = await fetch(`http://127.0.0.1:5001/api/reservations/${reservationId}/ics`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `reservation-${reservationId}.ics`;
    a.click();
    URL.revokeObjectURL(url);
}

export async function checkReminders(userId) {
    const response = await fetch(`http://127.0.0.1:5001/api/reservations/reminders/check?user_id=${userId}`);
    return await response.json();
}

// ==================== Notifications API ====================

export async function getNotifications(userId, unreadOnly = false) {
    const response = await fetch(`http://127.0.0.1:5001/api/notifications/?user_id=${userId}&unread_only=${unreadOnly}`);
    return await response.json();
}

export async function markNotificationRead(notificationId) {
    const response = await fetch(`http://127.0.0.1:5001/api/notifications/${notificationId}/read`, {
        method: "PUT",
    });
    return await response.json();
}

export async function markAllNotificationsRead(userId) {
    const response = await fetch(`http://127.0.0.1:5001/api/notifications/read-all?user_id=${userId}`, {
        method: "PUT",
    });
    return await response.json();
}

// ==================== Recommendations API ====================

export async function getRecommendations(userId, searchHistory = []) {
    const params = new URLSearchParams({ user_id: userId });
    if (searchHistory.length > 0) params.append("search_history", searchHistory.join(","));
    const response = await fetch(`http://127.0.0.1:5001/api/recommendations/?${params.toString()}`);
    return await response.json();
}
