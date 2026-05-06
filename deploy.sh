#!/bin/bash

# 1. Entrar na pasta do repositório no NAS
cd /volume1/docker/creative-portal-ilpdm

# 2. Sincronizar o Frontend com a pasta do Web Station
# Isto garante que o que editaste no Trae vai para o site real
cp ./frontend/index.html /volume1/web/staging/creative-portal/index.html

# 3. Reconstruir os containers do Backend (API e DB)
docker-compose up -d --build

# 4. Limpar recursos antigos
docker image prune -f

echo "✅ Deploy concluído: Frontend e Backend actualizados!"