#!/bin/sh

mkdir -p /var/log/amnezia /var/log/nginx /var/log/supervisor
chmod 755 /var/log/amnezia /var/log/nginx /var/log/supervisor
chmod -R 755 /app/web-ui/
chown :www-data /var/www/le
chmod -R 755 /var/www/le

lsmod | grep -E "^nf_tables|^nft_"
nft_true=$?

if [ "$nft_true" -ne 0 ]; then
    ln -sf /sbin/iptables-legacy /sbin/iptables
    echo "iptables-legacy set as default"
fi

NGINX_CONFIG_FILE="/etc/nginx/http.d/default.conf"
LE_CONFIG_FILE="/etc/letsencrypt/cli.ini"

if [ -n "$NGINX_PORT" ] && [ "$NGINX_PORT" != "80" ]; then
    echo "Configuring nginx to listen on port $NGINX_PORT"
    sed -i "1,/listen 80;/ s/listen 80;/listen $NGINX_PORT;/" $NGINX_CONFIG_FILE
fi

: "${NGINX_USER:=admin}"
: "${NGINX_PASSWORD:=changeme}"
htpasswd -bc /etc/nginx/.htpasswd "$NGINX_USER" "$NGINX_PASSWORD"

nginx -t

if [ -n "$SSL_EMAIL" ] && [ "$SSL_DOMAIN" ]; then
    mv /etc/nginx/http.d/ssl.conf.template /etc/nginx/http.d/ssl.conf
    nginx
    echo "Configuring certbot to use $SSL_EMAIL and $SSL_DOMAIN"
    sed -i "s/email_placeholder/$SSL_EMAIL/" $LE_CONFIG_FILE
    sed -i "s/domain_placeholder/$SSL_DOMAIN/" $LE_CONFIG_FILE

    certbot certonly -c $LE_CONFIG_FILE --non-interactive
    certbot certificates | grep VALID
    cert_valid=$?

    if [ "$cert_valid" -eq 0 ]; then
        sed -i \
            -e "1,/listen $NGINX_PORT;/ s/listen $NGINX_PORT;/listen $NGINX_PORT ssl;/" \
            -e "1,/server_name _;/ s/server_name _;/server_name $SSL_DOMAIN;/" \
            -e "/server_name $SSL_DOMAIN;/a\\
    # SSL certificate configuration\\
    ssl_certificate /etc/letsencrypt/live/$SSL_DOMAIN/fullchain.pem;\\
    ssl_certificate_key /etc/letsencrypt/live/$SSL_DOMAIN/privkey.pem;"\
            $NGINX_CONFIG_FILE

        certbot install --cert-name $SSL_DOMAIN

        sed -i "/ssl_certificate_key \/etc\/letsencrypt\/live\/$SSL_DOMAIN\/privkey.pem;/a\\
    include /etc/letsencrypt/options-ssl-nginx.conf;\\
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;" \
            $NGINX_CONFIG_FILE

        croncmd="/usr/bin/certbot renew --quiet --deploy-hook \"nginx -s reload\""
        cronjob="30 3 * * 2 $croncmd"
        ( crontab -l | grep -v -F "$croncmd" ; echo "$cronjob" ) | crontab -
        if [ $? -eq 0 ]; then
            echo "Cert renewal Cronjob successfully created"
            crontab -l | grep "$croncmd"
        fi
    fi
    nginx -s quit
fi

# Start supervisord
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf