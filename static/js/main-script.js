async function checkSession() {
    const response = await fetch('/session_status');
    const data = await response.json();
    const loginLink = document.getElementById('login-link');
    const usernameElement = document.getElementById('username');

    // Проверяем, что элементы существуют, чтобы избежать ошибок, если они не найдены
    if (!loginLink || !usernameElement) {
        console.error('Element not found');
        return;
    }

    if (data.authenticated) {
        loginLink.href = "/logout";
        loginLink.textContent = "Log out";
        usernameElement.textContent = data.username || "Guest";  // Защита от пустого значения

        // Обработчик для Log out без анимаций
        loginLink.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = loginLink.href;
        });
    } else {
        loginLink.href = "/login";
        loginLink.textContent = "Sign in";
        usernameElement.textContent = "Guest";

        // Обработчик для Log in без анимаций
        loginLink.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = loginLink.href;
        });
    }

    // Обработчик для всех кнопок и ссылок, кроме Log in/Log out
    document.querySelectorAll('a, button').forEach((element) => {
        if (element !== loginLink) {
            element.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.href = element.href;
            });
        }
    });
}

// Вызовем функцию при загрузке страницы
window.onload = checkSession;