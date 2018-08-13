docker network create --driver overlay --subnet=10.0.0.0/16 hpc-cluster-network
docker stack deploy -c docker-compose.yml hpc_cluster
