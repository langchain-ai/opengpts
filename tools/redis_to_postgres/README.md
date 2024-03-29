OpenGPTs previously used Redis for data persistence, but has since switched to Postgres. If you have data in Redis that you would like to migrate to Postgres, follow the instructions below.

Navigate to the `tools/redis_to_postgres` directory and ensure that the environment variables in the docker-compose file are set correctly for your Redis and Postgres instances. Then, run the following command to perform the migration:

```shell
docker compose up --build --abort-on-container-exit
```

This will run database schema migrations for Postgres and then copy data from Redis to Postgres. Eventually all containers will be stopped.

Note: if you were not using Redis locally and instead were using a remote Redis instance (for example on AWS), you can simply set the `REDIS_URL` environment variable to the remote instance's address, remove the `redis` service from the docker-compose file, and run the same command as above.