# Shell script to open an ssh tunnel to an elastic search
# cluster node hosted at Berkeley KBase.

# Parameterized by:
# IP - the ip address of the ES node machine
# SSHUSER - the dev's username for ssh
# SSHPASS - the dev's passowrd

sshpass -e ssh \
    -4 \
    -N \
    -o PubkeyAuthentication=no \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -o UserKnownHostsFile=/dev/null \
    -L "0.0.0.0:9500:${IP}:9500" \
    "${SSHUSER}@${SSHHOST}" 
 