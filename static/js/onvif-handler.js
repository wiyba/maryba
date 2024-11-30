// Проверка наличия картинки с камеры. Если картинка не загрузилась, то выводится сообщение об ошибке
document.addEventListener('DOMContentLoaded', () => {
    const img = document.querySelector('.video-stream');
    let hasLoaded = false;
    let timeout = 500;
    console.log("Ожидание картинки с '/onvif_source'. Таймаут равен", timeout, "мс" );

    img.addEventListener('load', () => {
        hasLoaded = true;
        if (img.naturalWidth === 0 || img.naturalHeight === 0) {
            showError();
        }
    });

    img.addEventListener('error', showError);

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
