import { login, register } from "../api-client.js";

console.log("app.js loaded successfully!");

const loginForm = document.getElementById("loginForm");
const signupForm = document.getElementById("signupForm");
const forgotForm = document.getElementById("forgotForm");

window.showSignup = function () {
    loginForm.classList.remove("active");
    forgotForm.classList.remove("active");
    signupForm.classList.add("active");
};

window.showLogin = function () {
    signupForm.classList.remove("active");
    forgotForm.classList.remove("active");
    loginForm.classList.add("active");
};

window.showForgot = function () {
    loginForm.classList.remove("active");
    signupForm.classList.remove("active");
    forgotForm.classList.add("active");
};

window.checkPasswordStrength = function () {
    const password = document.getElementById("signupPassword").value;
    const bar = document.getElementById("strength-bar");
    const text = document.getElementById("strength-text");

    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;

    if (strength <= 2) {
        bar.style.width = "33%";
        bar.style.background = "#e53e3e";
        text.textContent = "Weak password";
        text.style.color = "#e53e3e";
    } else if (strength <= 4) {
        bar.style.width = "66%";
        bar.style.background = "#dd6b20";
        text.textContent = "Medium strength password";
        text.style.color = "#dd6b20";
    } else {
        bar.style.width = "100%";
        bar.style.background = "#38a169";
        text.textContent = "Strong password";
        text.style.color = "#38a169";
    }
};

loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const loginUsername = document.getElementById("username").value;
    const loginPassword = document.getElementById("password").value;

    try {
        const result = await login(loginUsername, loginPassword);
        if (result.status === "success") {
            // Redirect to businesses page on successful login
            window.location.href = "businesses.html";
        } else {
            alert("Login failed: " + (result.message || "Unknown error"));
        }
    } catch (error) {
        alert("Login error: " + error.message);
    }
});

signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const signupUsername = document.getElementById("signupUsername").value;
    const signupEmail = document.getElementById("signupEmail").value;
    const signupPhonenumber =
        document.getElementById("signupPhonenumber").value;
    const signupPassword = document.getElementById("signupPassword").value;
    const signupFirstName = document.getElementById("signupFirstName").value;
    const signupLastName = document.getElementById("signupLastName").value;
    const signupCity = document.getElementById("signupCity").value;
    const signupCountry = document.getElementById("signupCountry").value;

    try {
        const result = await register(
            signupUsername,
            signupEmail,
            signupPhonenumber,
            signupPassword,
            signupFirstName,
            signupLastName,
            signupCity,
            signupCountry,
        );
        if (result.status === "success") {
            // Redirect to businesses page on successful registration
            window.location.href = "businesses.html";
        } else {
            alert(
                "Registration failed: " + (result.message || "Unknown error"),
            );
        }
    } catch (error) {
        alert("Registration error: " + error.message);
    }
});

forgotForm.addEventListener("submit", (e) => {
    e.preventDefault();
    alert("If the email exists, a reset link has been sent.");
    showLogin();
});

// Check URL hash on page load to show the correct form
window.addEventListener("DOMContentLoaded", () => {
    const hash = window.location.hash;
    if (hash === "#signup") {
        showSignup();
    } else if (hash === "#login") {
        showLogin();
    } else if (hash === "#forgot") {
        showForgot();
    }
    // If no hash or unrecognized hash, default to login (already active by default)
});
