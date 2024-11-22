## maryba (camera portal)
A website that was created to implement the idea of creating an intercom based on PM3 and an IP camera that works with ONVIF.
There is an account system and soon there will be the ability to interact with the reader itself.

### Installation and Updates
To install, update, or uninstall the maryba service, you can use the following commands:

#### Install

```sh
sudo bash -c "$(curl -sL http://raw.githubusercontent.com/wiyba/maryba/main/install.sh)" @ install
```

#### Update
```sh
sudo bash -c "$(curl -sL http://raw.githubusercontent.com/wiyba/maryba/main/install.sh)" @ update
```

#### Uninstall
```sh
sudo bash -c "$(curl -sL http://raw.githubusercontent.com/wiyba/maryba/main/install.sh)" @ uninstall
```

### Service Management
The `install.sh` script also provides system management commands for handling the service itself. This includes operations such as installation, updating, and removal of the project and Docker components. The commands are as follows:

- **Install**: Sets up Docker, pulls the necessary repository, builds the Docker image, and creates a systemd service.
- **Update**: Pulls the latest changes, rebuilds the Docker image, and restarts the systemd service.
- **Remove**: Stops the service, deletes the systemd configuration, Docker container, image, and all associated files.

These commands ensure that the `maryba` service runs smoothly and can be easily maintained.