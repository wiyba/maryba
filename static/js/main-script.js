async function checkSession() {
    // Получение JSON с API страницы /session_status
    const response = await fetch('/session_status');
    const data = await response.json();

    // Определение элементов кнопки и имени пользователя для взаимодействия
    const loginLink = document.getElementById('login-link');
    const usernameElement = document.getElementById('username');

    // Отображение информации о пользователе
    // Если поле authenticated в объекте data равно true, отображаем следующее:
    if (data.authenticated) {
        loginLink.href = "/logout";
        loginLink.textContent = "Выйти";
        usernameElement.textContent = data.username || "Гость";
    }
    // В противном случае отображаем следующее:
    else {
        loginLink.href = "/login";
        loginLink.textContent = "Войти";
        usernameElement.textContent = "Гость";
    }
}

window.onload = checkSession;
