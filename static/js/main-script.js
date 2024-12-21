async function checkSession() {
    const response = await fetch('/session_status');
    const data = await response.json();

    const loginLink = document.getElementById('login-link');
    const usernameElement = document.getElementById('username');

    // Отображение информации о пользователе
    if (data.authenticated) {
        loginLink.href = "/logout";
        loginLink.textContent = "Выйти";
        usernameElement.textContent = data.username || "Гость";
    } else {
        loginLink.href = "/login";
        loginLink.textContent = "Войти";
        usernameElement.textContent = "Гость";
    }
}

window.onload = checkSession;
