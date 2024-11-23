# Базовый образ Python
FROM python:3.10-slim

# Установим рабочую директорию
WORKDIR /app

# Скопируем файл зависимостей
COPY requirements.txt .

# Установим системные зависимости (включая libgl1 и libglib2.0-0)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Обновим pip
RUN pip install --upgrade pip

# Установим зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Скопируем весь проект в контейнер
COPY . .

# Откроем порт 8000
EXPOSE 8000

# Запустим приложение
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]