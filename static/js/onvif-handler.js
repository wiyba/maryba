document.addEventListener('DOMContentLoaded', () => {
    const img = document.querySelector('.video-stream');
    let hasLoaded = false;

    // Обработчик события load для проверки, была ли загружена картинка
    img.addEventListener('load', () => {
        hasLoaded = true;
        if (img.naturalWidth === 0 || img.naturalHeight === 0) {
            showError();
        }
    });

    // Обработчик события error для обработки ошибок загрузки
    img.addEventListener('error', showError);

    // Таймер для проверки статуса загрузки через 5 секунд
    setTimeout(() => {
        if (!hasLoaded) {
            showError();
        }
    }, 500);
});

function showError() {
    console.log("showError() вызвана");
    const img = document.querySelector('.video-stream');
    const errorMessage = document.getElementById('error-message');
    img.style.display = 'none';
    errorMessage.style.display = 'flex';
}
