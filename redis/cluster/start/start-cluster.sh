#!/bin/bash

REPLICAS=1
HOSTS=""

for HOSTNAME in "redis-cluster-1" "redis-cluster-2" "redis-cluster-3" "redis-cluster-4" "redis-cluster-5" "redis-cluster-6";
do
IP=$(getent hosts $HOSTNAME | awk '{ print $1 }')
HOSTS="$HOSTS $IP:6379"
done

echo "yes"| redis-cli --cluster create $HOSTS --cluster-replicas 1

while true;
do
sleep 10
done