// Изменение UID (идентефикатора карты MFP пользователя)
async function handleProfileSubmit(event) {
    event.preventDefault();

    const uid = document.querySelector('input[name="uid"]').value;

    // Проверка на длинну введенных данных
    if (uid === '') {
        alert('All fields must be filled in');
        event.preventDefault();
        return;
    }
    else if (uid.length !== 11) {
        alert('UID должен быть длиной в 8 символов');
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
        } else {
            const errorData = await response.json();
            alert(errorData.detail);
        }
    } catch (error) {
        console.error("Ошибка при изменении профиля:", error);
    }
}

// Удаление профиля
async function handleProfileDelete(event) {
    event.preventDefault();

    const confirmation = confirm("Are you sure you want to delete your account? This action cannot be undone.");

    try {
        const response = await fetch('/profile', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ confirmation: true })
        });

        if (response.ok) {
            window.location.href = "/logout";
        } else {
            const errorData = await response.json();
            alert(errorData.detail || "An error occurred while deleting the profile.");
        }
    } catch (error) {
        console.error("Ошибка при удалении профиля:", error);
    }
}

