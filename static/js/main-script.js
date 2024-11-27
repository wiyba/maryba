async function checkSession() {
    const response = await fetch('/session_status');
    const data = await response.json();

    const loginLink = document.getElementById('login-link');
    const usernameElement = document.getElementById('username');

    if (data.authenticated) {
        loginLink.href = "/logout";
        loginLink.textContent = "Log out";
        usernameElement.textContent = data.username || "Guest";
    } else {
        loginLink.href = "/login";
        loginLink.textContent = "Sign in";
        usernameElement.textContent = "Guest";
    }
}

window.onload = checkSession;
