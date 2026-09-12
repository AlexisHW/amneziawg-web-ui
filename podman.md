Here is a working `amneziawg-web-ui.container` quadlet:
```
[Container]
AddCapability=NET_ADMIN FOWNER CHOWN DAC_OVERRIDE SETGID SETUID
AddDevice=/dev/net/tun
ContainerName=amneziawg-web-ui
DropCapability=ALL
Environment=NGINX_PORT=8080
Environment=DEFAULT_PORT=51820
Environment=DEFAULT_DNS=1.1.1.1,8.8.8.8
Image=docker.io/alexishw/amneziawg-web-ui:latest
Mount=type=bind,source=/home/podman/.local/share/amneziawg-web-ui/data,destination=/etc/amnezia
PublishPort=8080:8080/tcp
PublishPort=51820:51820/udp
Pull=always
Sysctl=net.ipv4.ip_forward=1
Sysctl=net.ipv4.conf.all.src_valid_mark=1
AutoUpdate=registry
NoNewPrivileges=true

[Service]
Restart=always

[Unit]
After=network.target

[Install]
WantedBy=default.target
```