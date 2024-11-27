async function handleProfileSubmit(event) {
    event.preventDefault();

    const uid = document.querySelector('input[name="uid"]').value;

    if (uid === '') {
        alert('All fields must be filled in');
        event.preventDefault();
        return;
    }
    else if (uid.length !== 11) {
        alert('UID must be 8 characters long');
        event.preventDefault();
        return;
    }


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