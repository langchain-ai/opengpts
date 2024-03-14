FROM postgres:latest

RUN apt-get update && apt-get install -y git build-essential postgresql-server-dev-all

WORKDIR /tmp
RUN git clone --branch v0.6.1 https://github.com/pgvector/pgvector.git \
    && cd pgvector \
    && make \
    && make install

RUN apt-get remove -y git build-essential postgresql-server-dev-all && apt-get autoremove -y
RUN rm -rf /var/lib/apt/lists/* /tmp/pgvector