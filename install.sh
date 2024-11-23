#!/bin/bash
cd ~ || exit

SERVICE_NAME="maryba"
SERVICE_DESCRIPTION="Maryba Docker Service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
DOCKER_IMAGE="maryba:latest"
PORT="8000"
PROJECT_DIR="/opt/maryba"

ACTION=$1
if [[ -z "$ACTION" ]]; then
    echo "Usage: $0 [install|update|remove]"
    exit 1
fi

create_service() {
    echo "Создаём systemd-сервис для Docker-контейнера..."
    cat > $SERVICE_FILE <<EOF
[Unit]
Description=$SERVICE_DESCRIPTION
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/docker run --rm --name $SERVICE_NAME -p $PORT:8000 $DOCKER_IMAGE
ExecStop=/usr/bin/docker stop $SERVICE_NAME
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    echo "Перезагружаем конфигурацию systemd..."
    systemctl daemon-reload
}

install_service() {
    echo "Устанавливаем проект..."

    if ! command -v docker &> /dev/null; then
        echo "Docker not found. Installing..."
        curl -fsSL https://get.docker.com | bash
        sudo systemctl start docker
        sudo systemctl enable docker
    else
        echo "Docker is already installed."
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo "Docker Compose not found. Installing..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    else
        echo "Docker Compose is already installed."
    fi

    if docker ps -a --format '{{.Names}}' | grep -Eq "^$SERVICE_NAME\$"; then
        echo "Удаляем старый контейнер $SERVICE_NAME..."
        docker rm -f $SERVICE_NAME
    fi

    if docker images --format '{{.Repository}}:{{.Tag}}' | grep -Eq "^$DOCKER_IMAGE\$"; then
        echo "Удаляем старый Docker образ $DOCKER_IMAGE..."
        docker rmi $DOCKER_IMAGE
    fi

    if [ ! -d "$PROJECT_DIR" ]; then
        echo "Cloning repository..."
        git clone https://github.com/wiyba/maryba.git $PROJECT_DIR
    else
        echo "Repository already exists at $PROJECT_DIR. Pulling latest changes..."
        cd $PROJECT_DIR || exit
        git pull
    fi

    cd $PROJECT_DIR || exit

    echo "Building Docker image..."
    docker build -t $DOCKER_IMAGE .

    echo "Настройка systemd-сервиса..."
    create_service
    systemctl enable $SERVICE_NAME
    systemctl start $SERVICE_NAME
    echo "Сервис $SERVICE_NAME установлен и запущен! Сайт доступен на http://localhost:$PORT"

    echo "Введите домен для вашего сервиса:"
    read -r DOMAIN
    while [ -z "$DOMAIN" ]; do
        echo "Домен не может быть пустым. Повторите ввод:"
        read -r DOMAIN
    done

    # Создание локальной папки проекта
    STATIC_SRC="$SERVICE_NAME:$PROJECT_DIR/static"
    STATIC_DEST="/var/www/$DOMAIN"
    echo "Копируем статические файлы из контейнера $STATIC_SRC в $STATIC_DEST..."
    if [ -d "$STATIC_DEST" ]; then
        rm -rf "$STATIC_DEST"
    fi
    mkdir -p "$STATIC_DEST"
    docker cp "$SERVICE_NAME:/app/static" "$STATIC_DEST"

    # Создание конфигурации для проксирования nginx
    CURRENT_USER=$(whoami)
    ACME_DIR="$HOME/.acme.sh"
    ACME_SCRIPT="$ACME_DIR/acme.sh"
    SSL_PATH="/var/lib/$SERVICE_NAME/certs/key.pem"
    SSL_KEY="/var/lib/$SERVICE_NAME/certs/fullchain.pem"
    NGINX_CONFIG_PATH="/etc/nginx/sites-available/$DOMAIN"
    NGINX_CONFIG_LINK="/etc/nginx/sites-enabled/$DOMAIN"

    if [ -d "$ACME_DIR" ] && [ -f "$ACME_SCRIPT" ]; then
        echo "acme.sh уже установлен в $ACME_DIR."
    else
        echo "acme.sh не найден. В процессе установки введите свой email на который зарегистрирован домен."

        # Устанавливаем acme.sh
        curl https://get.acme.sh | sh -s email=EMAIL

        # Проверяем, успешно ли установлен
        if [ -f "$ACME_SCRIPT" ]; then
            echo "acme.sh успешно установлен в $ACME_DIR."
        else
            echo "Ошибка при установке acme.sh. Проверьте подключение к интернету и повторите попытку."
            exit 1
        fi
    fi

    if [ ! -x "$ACME_SCRIPT" ]; then
        chmod +x "$ACME_SCRIPT"
    fi

    if [ ! -f "$SSL_PATH" ] || [ ! -f "$SSL_KEY" ]; then
        echo "Сертификаты не найдены или не полные. Проверяем директорию $CERTS_DIR..."

        if [ ! -d "$CERTS_DIR" ]; then
            mkdir -p "$CERTS_DIR"
        fi

        if [ -f "$SSL_PATH" ]; then
            echo "Удаляем старый файл сертификата $SSL_PATH..."
            rm -f "$SSL_PATH"
        fi

        if [ -f "$SSL_KEY" ]; then
            echo "Удаляем старый файл ключа $SSL_KEY..."
            rm -f "$SSL_KEY"
        fi

        echo "Запрашиваем новые сертификаты для домена $DOMAIN..."
        ~/.acme.sh/acme.sh --set-default-ca --server letsencrypt \
            --issue --standalone \
            -d "$DOMAIN" \
            --key-file "$SSL_KEY" \
            --fullchain-file "$SSL_PATH"

        # Проверяем, успешно ли создан сертификат
        if [ -f "$SSL_PATH" ] && [ -f "$SSL_KEY" ]; then
            echo "Сертификаты успешно созданы и сохранены в $CERTS_DIR."
        else
            echo "Ошибка при создании сертификатов. Проверьте настройки acme.sh."
            exit 1
        fi
    else
        echo "Сертификаты уже существуют: $SSL_PATH и $SSL_KEY."
    fi

    echo "Создаём конфигурацию Nginx для домена $DOMAIN..."

    if [ -f "$NGINX_CONFIG_PATH" ]; then
        rm -f "$NGINX_CONFIG_PATH"
        rm -f "$NGINX_CONFIG_LINK"
    fi

    cat > "$NGINX_CONFIG_PATH" <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name $DOMAIN www.$DOMAIN;

    ssl_certificate /$CURRENT_USER/.acme.sh/${DOMAIN}_ecc/fullchain.cer;
    ssl_certificate_key /$CURRENT_USER/.acme.sh/${DOMAIN}_ecc/$DOMAIN.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    echo "Конфигурация Nginx создана: $NGINX_CONFIG_PATH"

    # Создаём символическую ссылку в sites-enabled
    if [ -f "$NGINX_CONFIG_LINK" ]; then
        echo "Удаляем старую символическую ссылку для $DOMAIN..."
        rm -f "$NGINX_CONFIG_LINK"
    fi

    ln -s "$NGINX_CONFIG_PATH" "$NGINX_CONFIG_LINK"

    # Проверяем конфигурацию Nginx
    echo "Проверяем конфигурацию Nginx..."
    nginx -t

    if [ $? -eq 0 ]; then
        echo "Перезапускаем Nginx..."
        systemctl reload nginx
        echo "Nginx успешно настроен и перезапущен!"
    else
        echo "Ошибка в конфигурации Nginx. Проверьте файл $NGINX_CONFIG_PATH."
    fi

}

update_service() {
    echo "Обновляем проект..."

    if docker ps -a --format '{{.Names}}' | grep -Eq "^$SERVICE_NAME\$"; then
      echo "Удаляем старый контейнер $SERVICE_NAME..."
      docker rm -f $SERVICE_NAME
    fi

    if docker images --format '{{.Repository}}:{{.Tag}}' | grep -Eq "^$DOCKER_IMAGE\$"; then
        echo "Удаляем старый Docker образ $DOCKER_IMAGE..."
        docker rmi $DOCKER_IMAGE
    fi

    if [ -d "$PROJECT_DIR" ]; then
        cd $PROJECT_DIR || exit
        echo "Pulling latest changes..."
        git pull
        echo "Rebuilding Docker image..."
        docker build -t $DOCKER_IMAGE .

        echo "Введите домен для вашего сервиса:"
        read -r DOMAIN
        while [ -z "$DOMAIN" ]; do
            echo "Домен не может быть пустым. Повторите ввод:"
            read -r DOMAIN
        done

        STATIC_SRC="$SERVICE_NAME:$PROJECT_DIR/static"
        STATIC_DEST="/var/www/$DOMAIN"
        echo "Копируем статические файлы из контейнера $STATIC_SRC в $STATIC_DEST..."
        mkdir -p "$STATIC_DEST"
        docker cp "$SERVICE_NAME:/app/static" "$STATIC_DEST"

        echo "Restarting service..."
        systemctl restart $SERVICE_NAME
        echo "Проект успешно обновлён!"
    else
        echo "Project directory not found. Please run install first."
        exit 1
    fi
}

uninstall_service() {
    echo "Удаляем сервис и проект..."
    systemctl stop $SERVICE_NAME
    systemctl disable $SERVICE_NAME
    rm -f $SERVICE_FILE
    systemctl daemon-reload
    echo "Сервис $SERVICE_NAME удалён."

    if docker ps -a --format '{{.Names}}' | grep -Eq "^$SERVICE_NAME\$"; then
        echo "Удаляем старый контейнер $SERVICE_NAME..."
        docker rm -f $SERVICE_NAME
    fi

    if docker images --format '{{.Repository}}:{{.Tag}}' | grep -Eq "^$DOCKER_IMAGE\$"; then
        echo "Удаляем старый Docker образ $DOCKER_IMAGE..."
        docker rmi $DOCKER_IMAGE
    fi

    if [ -d "$PROJECT_DIR" ]; then
        rm -rf "$PROJECT_DIR"
        echo "Проект удалён."
    else
        echo "Проект не найден."
    fi
}

case $ACTION in
    install)
        install_service
        ;;
    update)
        update_service
        ;;
    uninstall)
        uninstall_service
        ;;
    *)
        echo "Invalid action: $ACTION"
        echo "Usage: $0 [install|update|uninstall]"
        exit 1
        ;;
esac