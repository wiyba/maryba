#!/bin/bash
cd / || exit
LOGFILE="/var/log/maryba.log"
exec > >(tee -a "$LOGFILE") 2>&1
trap 'echo "Ошибка на строке $LINENO: Команда завершилась с кодом $?. Завершаем скрипт." >&2' ERR

SERVICE_NAME="maryba"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
PORT="8000"

PROJECT_DIR="/var/lib/$SERVICE_NAME"
CERTS_DIR="$PROJECT_DIR/../${SERVICE_NAME}_certs"
STATIC_DIR="$PROJECT_DIR/app/static"

ACTION=$1
if [[ -z "$ACTION" ]]; then
    echo "Использование: $0 [install|update|remove]"
    exit 1
fi

# Функция для проверки и установки программ
check_and_install() {
    local cmd=$1
    local package=$2
    if ! command -v "$cmd" &> /dev/null; then
        echo "$cmd не найден. Устанавливаем $package..."
        if [[ -f /etc/debian_version ]]; then
            sudo apt update
            sudo apt install -y "$package"
        elif [[ -f /etc/redhat-release ]]; then
            sudo yum install -y "$package"
        elif [[ -f /etc/arch-release ]]; then
            sudo pacman -Syu --noconfirm "$package"
        else
            echo "Неподдерживаемая ОС. Установка $package невозможна."
            exit 1
        fi
    else
        echo "$cmd уже установлен."
    fi
}

manage_nginx() {
    if command -v nginx &> /dev/null; then
        sudo systemctl "$1" nginx
    fi
}

create_service() {
    echo "Создаём systemd-сервис для Uvicorn..."
    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Maryba FastAPI Service
After=network.target

[Service]
Type=simple
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/main.py
Restart=always
Environment=ENV_FILE_PATH=$PROJECT_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

    echo "Перезагружаем конфигурацию systemd..."
    systemctl daemon-reload
}

install_nginx() {
    check_and_install nginx nginx

    while [[ -z "$DOMAIN" ]]; do
        read -r -p "Введите домен для настройки Nginx (не может быть пустым): " DOMAIN
    done

    echo "Создаём конфигурацию Nginx..."
    STATIC_DIR="$PROJECT_DIR/app/static"
    mkdir -p "$STATIC_DIR"

    SSL_PATH="$CERTS_DIR/fullchain.pem"
    SSL_KEY="$CERTS_DIR/key.pem"

    if [[ ! -f "$SSL_PATH" || ! -f "$SSL_KEY" ]]; then
        echo "Не найдены SSL сертификаты:"
        [[ ! -f "$SSL_PATH" ]] && echo "- Отсутствует файл: $SSL_PATH"
        [[ ! -f "$SSL_KEY" ]] && echo "- Отсутствует файл: $SSL_KEY"

        echo
        echo "Предлагается установить сертификаты с помощью команды:"
        echo "$HOME/.acme.sh/acme.sh --set-default-ca --server letsencrypt \\"
        echo "    --issue --standalone --force -d YOUR_DOMAIN \\"
        echo "    --key-file $SSL_KEY \\"
        echo "    --fullchain-file $SSL_PATH"
        echo

        while [[ ! "$install_cert_answer" =~ ^[YyNn]$ ]]; do
            read -r -p "Хотите ли вы установить сертификаты сейчас? [y/N]: " install_cert_answer
        done

        if [[ "$install_cert_answer" =~ ^[Yy]$ ]]; then
            echo "Устанавливаем сертификаты..."
            systemctl stop nginx
            mkdir -p "$CERTS_DIR"
            ~/.acme.sh/acme.sh --set-default-ca --server letsencrypt \
                --issue --standalone --force -d "$DOMAIN" \
                --key-file "$SSL_KEY" \
                --fullchain-file "$SSL_PATH" || {
                    echo "Ошибка при установке сертификатов. Проверьте установку acme.sh и повторите попытку."
                    exit 1
                }
            systemctl start nginx
            echo "Сертификаты успешно установлены."
        else
            echo "Сертификаты не установлены. Завершаем выполнение."
            exit 1
        fi
    fi

    SSL_PATH="$CERTS_DIR/fullchain.pem"
    SSL_KEY="$CERTS_DIR/key.pem"
    NGINX_CONFIG_PATH="/etc/nginx/sites-available/$DOMAIN.conf"
    NGINX_CONFIG_LINK="/etc/nginx/sites-enabled/$DOMAIN.conf"

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

    location /static/ {
        root $STATIC_DIR;
        autoindex on;
    }

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    rm "$NGINX_CONFIG_LINK"
    ln -s "$NGINX_CONFIG_PATH" "$NGINX_CONFIG_LINK"

    echo "Проверяем конфигурацию Nginx..."
    nginx -t
    manage_nginx restart
}

install_project() {
    echo "Проверяем наличие старой версии и удаляем её..."
    uninstall_project

    mkdir -p "$PROJECT_DIR"

    echo "Устанавливаем проект..."
    check_and_install git git
    check_and_install python3 python3

    # Клонирование репозитория
    git clone https://github.com/wiyba/maryba "$PROJECT_DIR"
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"

    # Активация виртуального окружения
    python3 -m venv "$PROJECT_DIR/venv"
    source "$PROJECT_DIR/venv/bin/activate"
    cd $PROJECT_DIR || exit
    pip install --no-cache-dir --upgrade pip
    pip install -r "$PROJECT_DIR/requirements.txt" || { echo "Ошибка установки Python-зависимостей"; exit 1; }

    create_service
    systemctl enable "$SERVICE_NAME"
    systemctl start "$SERVICE_NAME"

    echo "Хотите настроить Nginx? [y/N]: "
    while [[ ! "$install_nginx_answer" =~ ^[YyNn]$ ]]; do
        read -r install_nginx_answer
    done
    if [[ "$install_nginx_answer" =~ ^[Yy]$ ]]; then
        install_nginx
    fi
}

uninstall_project() {
    echo "Удаляем сервис и проект..."
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        systemctl stop "$SERVICE_NAME"
        systemctl disable "$SERVICE_NAME"
        rm -f "$SERVICE_FILE"
        systemctl daemon-reload
    fi

    rm -rf "$PROJECT_DIR"

    echo "Удалено."
}

case $ACTION in
    install)
        install_project
        ;;
    uninstall)
        uninstall_project
        ;;
    *)
        echo "Неверный параметр: $ACTION"
        exit 1
        ;;
esac