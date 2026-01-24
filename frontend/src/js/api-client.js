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
        const response = await fetch("http://127.0.0.1:5000/api/auth/logout", {
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
    const response = await fetch("http://127.0.0.1:5000/api/auth/login", {
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
    const response = await fetch("http://127.0.0.1:5000/api/auth/register", {
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

    const url = `http://127.0.0.1:5000/api/businesses?${params.toString()}`;

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
