async function handleSignUp(event) {
    event.preventDefault();

    // Создание переменных с данными из формы
    const username = document.querySelector('input[name="username"]').value;
    const password = document.querySelector('input[name="password"]').value;
    const password_confirm = document.querySelector('input[name="password_confirm"]').value;
    const security_key = document.querySelector('input[name="security_key"]').value;

    // Проверка на длинну введенных данных
    if (username === '' || password === '' || security_key === '') {
        alert('Все поля должны быть заполнены!');
        event.preventDefault();
        return;
    }
    else if (username.length < 4) {
        alert('Никнейм должен быть длиной хотя бы в 4 символа');
        event.preventDefault();
        return;
    }
    else if (password.length < 8) {
        alert('Пароль должен быть длиной хотя бы в 8 символов');
        event.preventDefault();
        return;
    }
    else if (password !== password_confirm) {
        alert('Пароли не совпадают');
        event.preventDefault();
        return;
    }
    else if (security_key.length !== 32) {
        alert('Секрет должен быть длиной в 32 символа');
        event.preventDefault();
        return;
    }

    // Отправка POST запроса с данными
    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({ username, password, security_key })
        });

        if (response.ok) {
            window.location.href = "/login";
        } else {
            const errorData = await response.json();
            alert(errorData.detail);
        }
    } catch (error) {
        console.error("Ошибка при регистрации:", error);
    }
}