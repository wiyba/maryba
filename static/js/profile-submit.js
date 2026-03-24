async function handleProfileSubmit(event) {
    event.preventDefault();

    const uid = document.querySelector('input[name="uid"]').value;

    if (uid === '') {
        alert('Все поля должны быть заполнены!');
        return;
    }
    if (uid.replace(/ /g, '').length < 4) {
        alert('UID слишком короткий');
        return;
    }

    try {
        const response = await fetch('/profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
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

async function handleProfileDelete(event) {
    event.preventDefault();

    if (!confirm("Вы уверены что хотите удалить свой аккаунт? Это действие не может быть отменено.")) {
        return;
    }

    try {
        const response = await fetch('/profile', { method: 'DELETE' });
        if (response.ok) {
            window.location.href = "/";
        } else {
            const errorData = await response.json();
            alert(errorData.detail || "Во время удаления аккаунта произошла ошибка.");
        }
    } catch (error) {
        console.error("Ошибка при удалении аккаунта:", error);
    }
}
