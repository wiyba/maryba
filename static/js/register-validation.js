async function handleSignUp(event) {
    event.preventDefault();

    const username = document.querySelector('input[name="username"]').value;
    const password = document.querySelector('input[name="password"]').value;
    const security_key = document.querySelector('input[name="security_key"]').value;

    if (username === '' || password === '' || security_key === '') {
        alert('All fields must be filled in');
        event.preventDefault();
        return;
    }
    else if (username.length < 4) {
        alert('Username must be at least 4 characters long');
        event.preventDefault();
        return;
    }
    else if (password.length < 8) {
        alert('Password must be at least 8 characters long');
        event.preventDefault();
        return;
    }
    else if (security_key.length !== 32) {
        alert('Security key must be 32 characters long');
        event.preventDefault();
        return;
    }


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