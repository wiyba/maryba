document.addEventListener('DOMContentLoaded', () => {
    const img = document.querySelector('.video-stream');
    let hasLoaded = false;
    let timeout = 500;
    console.log("Ожидание картинки с '/onvif_source'. Таймаут равен", timeout, "мс" );

    // Обработчик события load для проверки, была ли загружена картинка с камеры
    img.addEventListener('load', () => {
        hasLoaded = true;
        if (img.naturalWidth === 0 || img.naturalHeight === 0) {
            showError();
        }
    });

    // Обработчик события error для обработки ошибок загрузки картинки с камеры
    img.addEventListener('error', showError);

    // Таймер для проверки статуса загрузки через 0.5 секунды
    setTimeout(() => {
        if (!hasLoaded) {
            showError();
        }
    }, timeout);
});

function showError() {
    console.log("Ошибка загрузки картинки с камеры");
    const img = document.querySelector('.video-stream');
    const errorMessage = document.getElementById('error-message');
    img.style.display = 'none';
    errorMessage.style.display = 'flex';
}
