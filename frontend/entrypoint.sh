#!/bin/sh
# Injeta a URL da API no HTML em tempo de execução
if [ -n "$API_URL" ]; then
    sed -i "s|%%API_URL%%|${API_URL}|g" /usr/share/nginx/html/index.html
fi
exec nginx -g 'daemon off;'
