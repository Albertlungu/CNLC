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
export async function login(username, password) {
    const response = await fetch("http://127.0.0.1:5001/api/auth/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            username: username,
            password: password,
        }),
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
) {
    const response = await fetch("http://127.0.0.1:5001/api/auth/register", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            username: username,
            email: email,
            phone: phone,
            password: password,
            firstName: firstName,
            lastName: lastName,
            city: city,
            country: country,
        }),
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
