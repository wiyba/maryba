#!/bin/bash

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

    STATIC_SRC="$SERVICE_NAME:$PROJECT_DIR/static"
    STATIC_DEST="/var/www/$DOMAIN"
    echo "Копируем статические файлы из контейнера $STATIC_SRC в $STATIC_DEST..."
    mkdir -p "$STATIC_DEST"
    docker cp "$SERVICE_NAME:/app/static" "$STATIC_DEST"
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