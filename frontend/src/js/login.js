import { login, register, isLoggedIn } from "../api-client.js";

// Redirect to businesses page if already logged in
if (isLoggedIn()) {
    window.location.href = "businesses.html";
}

console.log("app.js loaded successfully!");

const loginForm = document.getElementById("loginForm");
const signupForm = document.getElementById("signupForm");
const forgotForm = document.getElementById("forgotForm");

// ==================== FORM SWITCHING ====================
window.showSignup = function () {
    loginForm.classList.remove("active");
    forgotForm.classList.remove("active");
    signupForm.classList.add("active");
    // Reset reCAPTCHA when switching forms
    if (typeof grecaptcha !== 'undefined') {
        grecaptcha.reset();
    }
};

window.showLogin = function () {
    signupForm.classList.remove("active");
    forgotForm.classList.remove("active");
    loginForm.classList.add("active");
    // Reset reCAPTCHA when switching forms
    if (typeof grecaptcha !== 'undefined') {
        grecaptcha.reset();
    }
};

window.showForgot = function () {
    loginForm.classList.remove("active");
    signupForm.classList.remove("active");
    forgotForm.classList.add("active");
};

// ==================== PASSWORD STRENGTH ====================
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

// ==================== reCAPTCHA VALIDATION ====================
function validateRecaptcha() {
    const recaptchaResponse = grecaptcha.getResponse();
    if (recaptchaResponse.length === 0) {
        alert("Please complete the reCAPTCHA verification");
        return false;
    }
    return recaptchaResponse;
}

// ==================== LOGIN FORM SUBMISSION ====================
loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    // Validate reCAPTCHA
    const recaptchaToken = validateRecaptcha();
    if (!recaptchaToken) {
        return;
    }
    
    const loginUsername = document.getElementById("username").value;
    const loginPassword = document.getElementById("password").value;

    try {
        // In production, you should verify the reCAPTCHA token on your backend
        // Send the token along with login credentials
        const result = await login(loginUsername, loginPassword);
        
        if (result.status === "success") {
            // Store session info in localStorage
            localStorage.setItem("session", JSON.stringify({
                username: loginUsername,
                userId: result.user.id,
                sessionInfo: result.session_info,
                loggedInAt: new Date().toISOString()
            }));
            // Redirect to businesses page on successful login
            window.location.href = "businesses.html";
        } else {
            alert("Login failed: " + (result.message || "Unknown error"));
            // Reset reCAPTCHA after failed login
            grecaptcha.reset();
        }
    } catch (error) {
        alert("Login error: " + error.message);
        // Reset reCAPTCHA on error
        grecaptcha.reset();
    }
});

// ==================== SIGNUP FORM SUBMISSION ====================
signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    // Validate reCAPTCHA
    const recaptchaToken = validateRecaptcha();
    if (!recaptchaToken) {
        return;
    }
    
    const signupUsername = document.getElementById("signupUsername").value;
    const signupEmail = document.getElementById("signupEmail").value;
    const signupPhonenumber = document.getElementById("signupPhonenumber").value;
    const signupPassword = document.getElementById("signupPassword").value;
    const signupFirstName = document.getElementById("signupFirstName").value;
    const signupLastName = document.getElementById("signupLastName").value;
    const signupCity = document.getElementById("signupCity").value;
    const signupCountry = document.getElementById("signupCountry").value;

    try {
        // In production, verify reCAPTCHA token on backend
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
            // Store session info in localStorage
            localStorage.setItem("session", JSON.stringify({
                username: signupUsername,
                userId: result.user.id,
                sessionInfo: result.session_info,
                loggedInAt: new Date().toISOString()
            }));
            // Redirect to businesses page on successful registration
            window.location.href = "businesses.html";
        } else {
            alert("Registration failed: " + (result.message || "Unknown error"));
            // Reset reCAPTCHA after failed signup
            grecaptcha.reset();
        }
    } catch (error) {
        alert("Registration error: " + error.message);
        // Reset reCAPTCHA on error
        grecaptcha.reset();
    }
});

// ==================== FORGOT PASSWORD FORM ====================
forgotForm.addEventListener("submit", (e) => {
    e.preventDefault();
    alert("If the email exists, a reset link has been sent.");
    showLogin();
});

// ==================== URL HASH ROUTING ====================
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