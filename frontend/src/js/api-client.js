// Login
export async function login(username, password) {
    const response = await fetch('http://127.0.0.1:5000/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    });
    const result = await response.json();
    console.log("Login function has been run.");
    console.log("RESULT: ", result);
    return result;
}

// Register
export async function register(username, email, phone, password, firstName, lastName, city, country) {
    const response = await fetch('http://127.0.0.1:5000/api/auth/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            email: email,
            phone: phone,
            password: password,
            firstName: firstName,
            lastName: lastName,
            city: city,
            country: country
        })
    });
    const result = await response.json();
    console.log("RESULT: ", result);
    return result;
}
