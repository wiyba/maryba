#!/bin/bash
cd ~ || exit

SERVICE_NAME="maryba"
SERVICE_DESCRIPTION="Maryba Docker Service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
DOCKER_IMAGE="maryba:latest"
PORT="8000"
PROJECT_DIR="/var/lib/$SERVICE_NAME"

ACTION=$1
if [[ -z "$ACTION" ]]; then
    echo "Использование: $0 [install|update|remove]"
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

install_ssl() {
    echo "Настраиваем SSL для домена $DOMAIN..."

    CERTS_DIR="/var/lib/$SERVICE_NAME/certs/"
    SSL_PATH="/var/lib/$SERVICE_NAME/certs/fullchain.pem"
    SSL_KEY="/var/lib/$SERVICE_NAME/certs/key.pem"

    # Проверяем существование сертификатов
    if [ ! -f "$SSL_PATH" ] || [ ! -f "$SSL_KEY" ]; then
        echo "Сертификаты не найдены. Запрашиваем новые сертификаты..."

        # Проверяем директорию
        [ ! -d "$CERTS_DIR" ] && mkdir -p "$CERTS_DIR"

        sudo systemctl stop nginx

        ~/.acme.sh/acme.sh --set-default-ca --server letsencrypt \
            --issue --standalone --force \
            -d "$DOMAIN" \
            --key-file "$SSL_KEY" \
            --fullchain-file "$SSL_PATH"

        sudo systemctl start nginx

        if [ -f "$SSL_PATH" ] && [ -f "$SSL_KEY" ]; then
            echo "Сертификаты успешно созданы!"
        else
            echo "Ошибка при создании сертификатов. Проверьте настройки."
            exit 1
        fi
    else
        echo "Сертификаты уже существуют."
    fi
}

install_nginx() {
    echo "Создаём конфигурацию Nginx для домена $DOMAIN..."

    # Удаляем старую конфигурацию, если она есть
    if [ -f "$NGINX_CONFIG_PATH" ]; then
        echo "Удаляем старую конфигурацию Nginx для $DOMAIN..."
        rm -f "$NGINX_CONFIG_PATH"
    fi

    if [ -f "$NGINX_CONFIG_LINK" ]; then
        echo "Удаляем старую символическую ссылку для $DOMAIN..."
        rm -f "$NGINX_CONFIG_LINK"
    fi

    # Создаём новую конфигурацию Nginx
    cat > "$NGINX_CONFIG_PATH" <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name $DOMAIN www.$DOMAIN;

    ssl_certificate $SSL_PATH;
    ssl_certificate_key $SSL_KEY;

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
    ln -s "$NGINX_CONFIG_PATH" "$NGINX_CONFIG_LINK"

    # Проверяем конфигурацию Nginx
    echo "Проверяем конфигурацию Nginx..."
    nginx -t

    # Если проверка прошла успешно, перезапускаем Nginx
    if [ $? -eq 0 ]; then
        echo "Перезапускаем Nginx..."
        systemctl reload nginx
        echo "Nginx успешно настроен и перезапущен!"
    else
        echo "Ошибка в конфигурации Nginx. Проверьте файл $NGINX_CONFIG_PATH."
        exit 1
    fi
}

install_service() {
    echo "Устанавливаем проект..."

    if ! command -v docker &> /dev/null; then
        echo "Docker не найден. Устанавливаем..."
        curl -fsSL https://get.docker.com | bash
        sudo systemctl start docker
        sudo systemctl enable docker
    else
        echo "Docker уже установлен."
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo "Docker Compose не найден. Устанавливаем..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    else
        echo "Docker Compose уже установлен."
    fi

    if docker ps -a --format '{{.Names}}' | grep -Eq "^$SERVICE_NAME\$"; then
        echo "Удаляем старый контейнер $SERVICE_NAME..."
        docker rm -f $SERVICE_NAME
    fi

    if docker images --format '{{.Repository}}:{{.Tag}}' | grep -Eq "^$DOCKER_IMAGE\$"; then
        echo "Удаляем старый образ $DOCKER_IMAGE..."
        docker rmi $DOCKER_IMAGE
    fi

    if [ ! -d "$PROJECT_DIR" ]; then
        echo "Клонируем репозиторий..."
        git clone https://github.com/wiyba/maryba.git $PROJECT_DIR
    else
        echo "Репозиторий уже существует. Обновляем..."
        cd $PROJECT_DIR || exit
        git pull
    fi
    cd $PROJECT_DIR || exit

    echo "Билдим образ Docker..."
    docker build -t $DOCKER_IMAGE .

    echo "Настройка systemd-сервиса..."
    create_service
    systemctl enable $SERVICE_NAME
    systemctl start $SERVICE_NAME

    echo "Введите домен для вашего сервиса:"
    read -r DOMAIN
    while [ -z "$DOMAIN" ]; do
        echo "Домен не может быть пустым. Повторите ввод:"
        read -r DOMAIN
    done

    echo "Хотите ли вы автоматически установить SSL для $DOMAIN? [y/N]:"
    read -r install_ssl_answer
    if [[ "$install_ssl_answer" =~ ^[Yy]$ ]]; then
        install_ssl
    else
        echo "Установка SSL пропущена."
    fi

    install_nginx
}

update_service() {
    echo "Обновляем проект..."
    # Код обновления...
}

uninstall_service() {
    echo "Удаляем проект..."
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
        echo "Невалидный параметр: $ACTION"
        echo "Использование: $0 [install|update|uninstall]"
        exit 1
        ;;
esac