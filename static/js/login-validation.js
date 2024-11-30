async function handleLogin(event) {
    event.preventDefault();

    const username = document.querySelector('input[name="username"]').value;
    const password = document.querySelector('input[name="password"]').value;

    // Проверка на длинну введенных данных
    if (username === '' || password === '') {
        alert('All fields must be filled in');
        event.preventDefault();
        return;
    }

    // Отправка POST запроса с данными
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({ username, password })
        });

        if (response.ok) {
            window.location.href = "/";
        } else {
            const errorData = await response.json();
            alert(errorData.detail);
        }
    } catch (error) {
        console.error("Ошибка при попытке входа:", error);
    }
}