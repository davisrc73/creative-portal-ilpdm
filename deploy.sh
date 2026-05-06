#!/bin/bash

# 1. Entrar na pasta do projeto no NAS
cd /volume1/docker/creative-portal-ilpd

# 2. Puxar a versão mais recente do GitHub
git pull origin main

# 3. Reconstruir e reiniciar os contentores
# O --build garante que as mudanças no backend/ são aplicadas
docker-compose up -d --build

# 4. Limpar imagens antigas para poupar espaço no NAS
docker image prune -f

echo "Deploy concluído com sucesso no @ilovepauldomar Creative Portal!"