#!/bin/bash
cd ~ || exit
LOGFILE="/var/log/$SERVICE_NAME.log"
exec > >(tee -a "$LOGFILE") 2>&1
trap 'echo "Ошибка на строке $LINENO: Команда завершилась с кодом $?. Завершаем скрипт." >&2' ERR

SERVICE_NAME="maryba"
SERVICE_DESCRIPTION="Maryba Docker Service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
DOCKER_IMAGE="maryba:latest"
PORT="8000"

PROJECT_DIR="/var/lib/$SERVICE_NAME"
CERTS_DIR="/var/lib/$SERVICE_NAME/certs/"
SSL_PATH="/var/lib/$SERVICE_NAME/certs/fullchain.pem"
SSL_KEY="/var/lib/$SERVICE_NAME/certs/key.pem"

ACTION=$1
if [[ -z "$ACTION" ]]; then
    echo "Использование: $0 [install|update|remove]"
    exit 1
fi

# Проверка установок
if ! command -v nginx &> /dev/null; then
    NGINX=0
else
    NGINX=1
fi

manage_nginx() {
    if [ "$NGINX" -eq 1 ]; then
        sudo systemctl "$1" nginx
    fi
}

if [ ! -d "$HOME/.acme.sh" ]; then
    ACME=0
else
    ACME=1
fi

if [ ! -f "$SERVICE_FILE" ]; then
    SERVICE=0
else
    SERVICE=1
fi

if ! command -v docker &> /dev/null; then
    DOCKER=0
else
    DOCKER=1
fi

if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMP=0
else
    DOCKER_COMP=1
fi

if ! command -v git &> /dev/null; then
    GIT=0
else
    GIT=1
fi


# Создание сервиса для контейнера
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

# Установка SSL сертефикатов
install_ssl() {
    echo
    echo
    if [ "$ACME" -eq 0 ]; then
        echo "acme.sh не установлен"
        echo
        echo "Установите с помощью:"
        echo "curl https://get.acme.sh | sh -s email=EMAIL"
        return 1
    fi

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
    manage_nginx stop
    ~/.acme.sh/acme.sh --set-default-ca --server letsencrypt \
        --issue --standalone --force \
        -d "$DOMAIN" \
        --key-file "$SSL_KEY" \
        --fullchain-file "$SSL_PATH" || {
        echo "Ошибка при запросе сертификатов. Проверьте настройки acme.sh."
        manage_nginx start
        return 1
        }
    manage_nginx start
    if [ -f "$SSL_PATH" ] && [ -f "$SSL_KEY" ]; then
        echo "Сертификаты успешно созданы и сохранены в $CERTS_DIR."
    else
        echo "Ошибка при создании сертификатов. Проверьте настройки acme.sh."
        return 1
    fi
    return 0
}

# Установка конфига nginx
install_nginx() {
    echo
    echo
    if [ "$NGINX" -eq 0 ]; then
        echo "Nginx не найден. Устанавливаем..."

        if [[ -f /etc/debian_version ]]; then
            sudo apt update
            sudo apt install -y nginx
        elif [[ -f /etc/redhat-release ]]; then
            sudo yum install -y epel-release
            sudo yum install -y nginx
        else
            echo "Неподдерживаемая ОС. Установка Nginx невозможна."
            return 1
        fi

        sudo systemctl start nginx
        sudo systemctl enable nginx
        echo "Nginx успешно установлен и запущен."
    else
        echo "Nginx уже установлен."
    fi

    echo "Создаём конфигурацию Nginx для домена $DOMAIN..."

    rm -f "$NGINX_CONFIG_PATH"
    rm -f "$NGINX_CONFIG_LINK"

    cat > "$NGINX_CONFIG_PATH" <<EOF
server {
    listen $IP:80;
    server_name $DOMAIN www.$DOMAIN;

    return 301 https://\$host\$request_uri;
}

server {
    listen $IP:443 ssl;
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
    ln -s "$NGINX_CONFIG_PATH" "$NGINX_CONFIG_LINK"

    echo "Проверяем конфигурацию Nginx..."
    nginx -t

    if nginx -t; then
        echo "Перезапускаем Nginx..."
        manage_nginx stop
        manage_nginx start
        echo "Nginx успешно настроен и перезапущен!"
    else
        echo "Ошибка в конфигурации Nginx. Проверьте файл $NGINX_CONFIG_PATH."
    fi
}


install_project() {
    echo "Проверяем наличие старой версии и удаляем её..."
    uninstall_project

    echo "Устанавливаем сайт..."

    # Проверка установки Docker
    if [ "$DOCKER" -eq 0 ]; then
        echo "Docker не найден. Устанавливаем..."
        curl -fsSL https://get.docker.com | bash
        sudo systemctl start docker
        sudo systemctl enable docker
    else
        echo "Docker уже установлен."
    fi

    # Проверка установки Docker Compose
    if [ "$DOCKER_COMP" -eq 0 ]; then
        echo "Docker Compose не найден. Устанавливаем..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    else
        echo "Docker Compose уже установлен."
    fi

    # Проверка установки Git
    if [ "$GIT" -eq 0 ]; then
        echo "Git не установлен. Устанавливаем..."

        if [[ -f /etc/debian_version ]]; then
            sudo apt update
            sudo apt install -y git

        elif [[ -f /etc/redhat-release ]]; then
            sudo yum install -y git

        elif [[ -f /etc/arch-release ]]; then
            sudo pacman -Syu --noconfirm git
        else
            echo "Неподдерживаемая ОС. Установка Git невозможна."
            exit 1
        fi

        echo "Git успешно установлен."
    else
        echo "Git уже установлен."
    fi

    # Репозиторий
    if [ ! -d "$PROJECT_DIR" ]; then
        echo "Клонируем репозиторий..."
        git clone https://github.com/wiyba/maryba.git $PROJECT_DIR
    else
        echo "Repository already exists at $PROJECT_DIR. Pulling latest changes..."
        cd $PROJECT_DIR || exit
        git pull
    fi
    cd $PROJECT_DIR || exit

    # Образ Docker
    echo "Билдим образ Docker..."
    docker build -t $DOCKER_IMAGE .

    # Настройка сервиса
    echo "Настройка systemd-сервиса..."
    create_service
    systemctl enable $SERVICE_NAME
    systemctl start $SERVICE_NAME

    echo "Сервис $SERVICE_NAME установлен и запущен! Сайт доступен на http://localhost:$PORT"
    echo
    echo

    read -r -p "Хотите ли вы автоматически установить SSL? [y/N]: " install_ssl_answer
    read -r -p "Хотите ли вы автоматически настроить nginx? [y/N]: " install_nginx_answer

    # Установка SSL
    if [[ "$install_ssl_answer" =~ ^[Yy]$ ]]; then
        while [[ -z "$DOMAIN" ]]; do
            read -r -p "Введите домен для установки SSL (не может быть пустым): " DOMAIN
        done

        if [[ -z "$DOMAIN" ]]; then
            echo "Ошибка: домен не может быть пустым для установки SSL."
            exit 1
        fi

        install_ssl
    else
        echo "Установка SSL пропущена."
    fi

    # Настройка Nginx
    if [[ "$install_nginx_answer" =~ ^[Yy]$ ]]; then
        while [[ -z "$DOMAIN" ]]; do
            read -r -p "Введите домен для настройки Nginx (не может быть пустым): " DOMAIN
        done

        while [[ -z "$IP" ]]; do
            read -r -p "Введите IP-адрес для настройки Nginx (не может быть пустым): " IP
        done
        STATIC_SRC="$SERVICE_NAME:/app/static"
        WEB_PROJECT_DIR="/var/www/$DOMAIN"
        NGINX_CONFIG_PATH="/etc/nginx/sites-available/$DOMAIN"
        NGINX_CONFIG_LINK="/etc/nginx/sites-enabled/$DOMAIN"

        if [[ -z "$DOMAIN" || -z "$IP" ]]; then
            echo "Ошибка: домен и IP-адрес не могут быть пустыми для настройки Nginx."
            exit 1
        fi

        # Копируем статические файлы
        echo "Копируем статические файлы из контейнера в $WEB_PROJECT_DIR..."
        rm -rf "$WEB_PROJECT_DIR"
        mkdir -p "$WEB_PROJECT_DIR"
        docker cp "$STATIC_SRC" "$WEB_PROJECT_DIR"

        install_nginx
    else
        echo "Настройка Nginx пропущена."
    fi
    docker logs $SERVICE_NAME
}


uninstall_project() {
    echo "Удаляем сервис и проект..."
    if [ "$SERVICE" -eq 1 ]; then
        systemctl stop $SERVICE_NAME
        systemctl disable $SERVICE_NAME
        rm -f $SERVICE_FILE
        systemctl daemon-reload
        echo "Сервис $SERVICE_NAME удалён."
    else
        echo "Сервис $SERVICE_NAME отсутствует."
    fi

    if docker images --format '{{.Repository}}:{{.Tag}}' | grep -Eq "^$DOCKER_IMAGE\$"; then
        echo "Удаляем образ $DOCKER_IMAGE..."
        docker rmi $DOCKER_IMAGE
    fi

    rm -rf "$WEB_PROJECT_DIR"
    rm -rf "$PROJECT_DIR"
}

case $ACTION in
    install)
        install_project
        ;;
    uninstall)
        uninstall_project
        ;;
    *)
        echo "Невалидный параметр: $ACTION"
        echo "Использование: $0 [install|uninstall]"
        exit 1
        ;;
esac