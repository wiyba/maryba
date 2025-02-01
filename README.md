# Maryba

Веб-сервис для безопасной системы RFID-доступа и видеонаблюдения (Proxmark3 и камера по ONVIF) в офисе, на складе или в любом другом объекте, где нужно контролировать вход и следить за ситуацией.

#### Чтобы установить, обновить или удалить сервис, используй команды ниже:

### Установка
```sh
sudo bash -c "$(curl -sL https://raw.githubusercontent.com/wiyba/maryba/main/setup.sh)" @ install
```

### Удаление
```sh
sudo bash -c "$(curl -sL https://raw.githubusercontent.com/wiyba/maryba/main/setup.sh)" @ uninstall
```

## Дополнительная информация

При необходимости можно установить acme.sh с помощью curl https://get.acme.sh | sh -s email=EMAIL.
Для просмотра логов можно использовать tail -f /var/lib/maryba/server.log или bash /var/lib/maryba/setup.sh logs.
