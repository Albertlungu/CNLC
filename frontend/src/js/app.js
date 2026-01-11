const loginForm = document.getElementById("loginForm");
const signupForm = document.getElementById("signupForm");
const forgotForm = document.getElementById("forgotForm");

function showSignup() {
  loginForm.classList.remove("active");
  forgotForm.classList.remove("active");
  signupForm.classList.add("active");
}

function showLogin() {
  signupForm.classList.remove("active");
  forgotForm.classList.remove("active");
  loginForm.classList.add("active");
}

function showForgot() {
  loginForm.classList.remove("active");
  signupForm.classList.remove("active");
  forgotForm.classList.add("active");
}

function checkPasswordStrength() {
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
}

loginForm.addEventListener("submit", e => {
  e.preventDefault();
  alert("Login submitted");
});

signupForm.addEventListener("submit", e => {
  e.preventDefault();
  alert("Account created");
});

forgotForm.addEventListener("submit", e => {
  e.preventDefault();
  alert("If the email exists, a reset link has been sent.");
  showLogin();
});
