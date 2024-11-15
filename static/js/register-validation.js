async function handleSignUp(event) {
    event.preventDefault(); // Предотвращаем переход по ссылке

    const username = document.querySelector('input[name="username"]').value;
    const password = document.querySelector('input[name="password"]').value;

    if (username.length < 4) {
        alert('Username must be at least 4 characters long');
        event.preventDefault();
        return;
    }
    else if (password.length < 8) {
        alert('Password must be at least 8 characters long');
        event.preventDefault();
        return;
    }

    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({ username, password })
        });

        if (response.ok) {
            window.location.href = "/login"; // Перенаправление на страницу входа при успешной регистрации
        } else {
            const errorData = await response.json();
            alert(errorData.detail); // Выводим сообщение об ошибке
        }
    } catch (error) {
        console.error("Ошибка при регистрации:", error);
    }
}