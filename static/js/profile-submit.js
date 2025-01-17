// Изменение UID (идентефикатора карты MFP пользователя)
async function handleProfileSubmit(event) {
    event.preventDefault();

    // Создание переменных с данными из формы
    const uid = document.querySelector('input[name="uid"]').value;

    // Проверка на длинну введенных данных
    if (uid === '') {
        alert('Все поля должны быть заполнены!');
        event.preventDefault();
        return;
    }
    else if (uid.length !== 11) {
        alert('UID должен быть длиной в 8 символов!');
        event.preventDefault();
        return;
    }

    // Отправка POST запроса с данными
    try {
        const response = await fetch('/profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({ uid })
        });

        if (response.ok) {
            window.location.href = "/";
        }
        else {
            const errorData = await response.json();
            alert(errorData.detail);
        }
    }
    catch (error) {
        console.error("Ошибка при изменении профиля:", error);
    }
}

// Удаление профиля
async function handleProfileDelete(event) {
    event.preventDefault();

    const confirmation = confirm("Вы уверены что хотите удалить свой аккаунт? Это действие не может быть отменено.");

    // Если confirmation == true то отправляется DELETE запрос
    if (confirmation) {
        try {
            const response = await fetch('/profile', {
                method: 'DELETE',
            });
            if (response.ok) {
                window.location.href = "/";
            } else {
                const errorData = await response.json();
                alert(errorData.detail || "Во время удаления аккаунта произошла ошибка.");
            }
        }
        catch (error) {
            console.error("Ошибка при удалении аккаунта:", error);
        }
    }
}

