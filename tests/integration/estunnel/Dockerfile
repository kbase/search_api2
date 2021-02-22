FROM alpine:3.13

# This image is dedicated to running an SSH tunnel from
# the docker network to an ES server node.

# We use sshpass to enable ssh to take a password from an environment variable
RUN apk upgrade --update-cache --available && \
    apk add --update --no-cache openssh sshpass && \
    mkdir -p /kb

COPY ./tunnel.sh /kb

EXPOSE 9500

WORKDIR /kb

ENTRYPOINT [ "/bin/sh" ]

CMD [ "/kb/tunnel.sh" ]