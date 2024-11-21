interface SessionStatus {
    authenticated: boolean;
    username: string;
}

async function checkSession() {
    const response: Response = await fetch('/session_status');
    const data: SessionStatus = await response.json(); // Используем типизированные данные

    const loginLink = document.getElementById('login-link') as HTMLAnchorElement; // Явное указание типа
    const usernameElement = document.getElementById('username') as HTMLElement;

    if (data.authenticated) {
        loginLink.href = "/logout";  // Теперь TypeScript знает, что это ссылка и у неё есть свойство href
        loginLink.textContent = "Log out";
        usernameElement.textContent = data.username || "Guest";
    } else {
        loginLink.href = "/login";
        loginLink.textContent = "Sign in";
        usernameElement.textContent = "Guest";
    }
}

window.onload = checkSession;

