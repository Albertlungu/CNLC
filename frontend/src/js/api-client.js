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


export async function filterBusinesses(category, lat1, lon1, radius, offset = 0, limit = 30) {

    const params = new URLSearchParams();
    if (category) {
        params.append('category', category);
    }
    if (lat1 && lon1 && radius) {
        params.append('lat1', lat1);
        params.append('lon1', lon1);
        params.append('radius', radius);
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
