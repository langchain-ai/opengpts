# Can't use the migrate/migrate image like we do for Postgres because it doesn't
# support sqlite3 driver by default. We need to install it via Go toolchain:
# https://github.com/golang-migrate/migrate/issues/899#issuecomment-1483741684
#
# Using the alpine3.18 tag because of: https://github.com/nkanaev/yarr/issues/187

FROM golang:alpine3.18
RUN apk add build-base
RUN go install -tags 'sqlite3' github.com/golang-migrate/migrate/v4/cmd/migrate@v4.17.1
WORKDIR /backend