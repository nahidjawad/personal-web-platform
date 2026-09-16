# Operations Guide

For the daily encrypted backup, weekly repository maintenance, Healthchecks alerts and isolated restoration procedure, see [Backups and recovery](backups.md).

## Scope

This guide contains tested operational procedures for the personal web
platform. It will expand as the application stack, backups and monitoring are
implemented.


## Check Docker service state

Connect to the server and run:

```bash
sudo systemctl status docker
```
For a machine-readable result:
```bash
sudo systemctl is-active docker
sudo systemctl is-enabled docker
```
Expected results are active and enabled.

## Inspect Docker

Show Docker runtime information:
```bash
sudo docker info
```
Show running containers:
```bash
sudo docker ps
```
Show running and stopped containers:
```bash
sudo docker ps --all
```
Show downloaded images:
```bash
sudo docker image ls
```
Show Docker disk usage:
```bash
sudo docker system df
```
## Inspect Docker service logs

Show recent daemon logs:
```bash
sudo journalctl --unit docker --since today
```
Follow new Docker daemon messages:
```bash
sudo journalctl --unit docker --follow
```
Press Ctrl+C to stop following the log.

## Restart Docker

A manual Docker restart should be exceptional:
```bash
sudo systemctl restart docker
```
Before restarting Docker on a production server, check the running containers
and understand the potential application impact:
```bash
sudo docker ps
```
The Ansible-managed live-restore setting allows running containers to remain
active during some daemon interruptions, but it is not a replacement for
normal maintenance planning.

## Check host resources

Check memory and swap:
```bash
free -h
swapon --show
```
Check filesystem usage:
```bash
df -h
```
Check listening ports:
```bash
sudo ss --tcp --udp --listening --processes --numeric
```
## Docker Compose configuration

Change to the application directory:

```bash
cd /srv/personal-web-platform
```
Validate the deployed configuration:
```bash
sudo docker compose --env-file .env config --quiet
```
List the defined services:
```bash
sudo docker compose --env-file .env config --services
```
List the defined persistent volumes:
```bash
sudo docker compose --env-file .env config --volumes
```
## Operate the application stack

Run Compose commands from the deployment directory:

```bash
cd /srv/personal-web-platform
```

Check service state:

```bash
sudo docker compose --env-file .env ps
```

Follow logs:
```bash
sudo docker compose --env-file .env logs --follow
```
Start or reconcile the stack:
```bash
sudo docker compose --env-file .env up --detach --wait
```
Stop containers while retaining named volumes:
```bash
sudo docker compose --env-file .env down
```
Recreate WordPress while retaining persistent content:
```bash
sudo docker compose --env-file .env up \
  --detach --no-deps --force-recreate --wait wordpress
```
Validate Nginx and the health endpoint:
```bash
sudo docker compose exec proxy nginx -t
curl --fail http://127.0.0.1/platform-health
```

## Inspect origin TLS

Validate the running Nginx configuration:

```bash
cd /srv/personal-web-platform
sudo docker compose --env-file .env exec proxy nginx -t
```

Inspect the Origin CA certificate without displaying the private key:

```bash
sudo openssl x509 \
  -in /srv/personal-web-platform/secrets/tls/chintavabna-origin.pem \
  -noout \
  -subject \
  -issuer \
  -dates \
  -ext subjectAltName
```

Confirm that the certificate is valid and covers `chintavabna.com` and
`*.chintavabna.com`.

Cloudflare does not send expiration notifications for Origin CA certificates.
The expiration date must therefore be tracked operationally.

## Verify the public production path

Confirm Cloudflare and the new origin health endpoint:

```bash
curl --silent --show-error --head https://chintavabna.com/ |
grep -Ei '^(HTTP/|server:|cf-ray:|location:)'

curl --fail --silent https://chintavabna.com/platform-health
```
The response headers should identify Cloudflare, and the health endpoint should
return `ok`.

Check the application after a deployment or infrastructure change:
```bash
curl --fail --silent https://chintavabna.com/
curl --fail --silent https://chintavabna.com/books/ >/dev/null
curl --fail --silent https://chintavabna.com/robots.txt >/dev/null
curl --fail --silent https://chintavabna.com/llms.txt >/dev/null
```
## Cutover rollback

The old origin address must be recorded privately outside Git during the
rollback window.

To return Cloudflare traffic to the legacy origin:

1. Create an emergency database dump from the new platform if it may have accepted new writes.
2. Edit only the proxied apex A record in Cloudflare.
3. Restore its target to the recorded legacy origin address.
4. Keep the record proxied.
5. Leave the www, MX, SES, SPF, DKIM and DMARC records unchanged.
6. Verify the public application and email delivery.

A rollback after the new platform accepts writes creates database divergence.
Those writes must be reconciled before another cutover.
