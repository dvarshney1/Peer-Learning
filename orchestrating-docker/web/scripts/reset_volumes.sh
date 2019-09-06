#!/usr/bin/env bash

./web/scripts/clear_logs.sh
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker volume rm $(docker volume ls -q)
