# ssh tunnel to elasticsearch host in a container

The searchapi2, when running locally in a container, it needs an ssh tunnel into the KBase network pointing to an ES cluster host.

The default way to do this is with an ssh tunnel running on the host, which is accessed by the searchapi2 service running in a container via Docker.

However, this does not work for macOS, nor with integration with a local kbase-ui instance when using working on searchapi2 in tandem with an kbase-ui hosted tool.

One option is to use `host.docker.internal`, instead of `localhost` in the searchapi2 container. However, this does not work when using a custom network which is required for working with kbase-ui.

The Docker image defined in this directory supports running an ssh tunnel for elastsearch within the container itself. 

Besides solving the issues described above, this tool also takes care of dependencies for us.

## Usage

```bash
IP="<ES_CLUSTER_HOST_IP>" SSHHOST="<KBASE_LOGIN_HOST>" SSHUSER="<KBASE_DEV_ACCOOUNT_USERNAME>" SSHPASS="<KBASE_DEV_ACCOUNT_PASSWORD>" docker run --rm -p 9500:9500 -e IP -e SSHUSER -e SSHPASS --name estunnel --network kbase-dev dev_estunnel
```

where the following environment variables must be set:

- `ES_CLUSTER_HOST_IP` is the IP address of one of the hosts in a CI eslasticsearch cluster
- `SSHHOST` is the host name to connect to for ssh tunneling.
- `SSHHUSER` is the username for your KBase developer account. Only internal KBase developers may use this tool
- `SSHPASS` is the plain-text password for the account provided above
