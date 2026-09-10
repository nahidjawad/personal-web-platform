# Project Status

## Current phase

Phase 7 complete: Cloudflare Origin CA TLS is configured on the new server and
pre-DNS HTTPS testing has passed.

## Overall completion

58% complete: 7 of 12 phases have passed verification.

## Completed

### Lightsail infrastructure

- Created AWS Lightsail instance `personal-web-prod-01`
- Selected Mumbai region
- Selected Ubuntu 24.04 LTS OS-only blueprint
- Selected 4 GB RAM, 2 vCPU and 80 GB SSD plan
- Attached a static IPv4 address
- Configured the Lightsail firewall for TCP ports 22, 80 and 443
- Verified Ubuntu, CPU, memory and disk capacity

### Ansible controller

- Installed `uv` in WSL 2
- Pinned controller Python to 3.12
- Installed Ansible Core and Ansible Lint
- Created local production and safe example inventories
- Secured the Lightsail SSH key outside the repository
- Verified SSH host identity
- Verified Ansible connectivity with `ansible.builtin.ping`

### Host baseline

- Recorded the untouched server preflight state
- Installed all available Ubuntu package updates
- Installed baseline administration packages
- Configured the server timezone as UTC
- Performed and verified a controlled reboot through Ansible
- Confirmed the baseline playbook is idempotent
- Created and activated a persistent 2 GiB swap file
- Configured `vm.swappiness` to 10
- Confirmed the swap role is idempotent
- Configured UFW with a default-deny inbound policy
- Enabled rate-limited SSH access on TCP 22
- Allowed temporary HTTP access on TCP 80
- Allowed temporary HTTPS access on TCP 443
- Enabled low-volume UFW logging
- Verified SSH access remained available after enabling UFW
- Confirmed the security role is idempotent

### Docker platform

- Added Docker's official Ubuntu package repository
- Installed Docker Engine from the official repository
- Installed the Docker Compose plugin
- Installed the Docker Buildx plugin
- Enabled Docker to start at boot
- Configured bounded `json-file` container logging
- Enabled Docker live restore
- Kept administrative Docker access behind privilege escalation
- Verified the runtime using the disposable `hello-world` container
- Confirmed the Docker role is idempotent
- Documented host deployment and initial Docker operations

### Compose platform foundation

- Created the application deployment directories through Ansible
- Set `/srv/personal-web-platform` as the deployment root
- Created the Nginx configuration directories
- Restricted the secrets directory to root
- Confirmed the Compose platform role is idempotent
- Defined Nginx, WordPress Apache and MariaDB services
- Separated frontend and private backend container networks
- Defined persistent WordPress and MariaDB named volumes
- Configured file-based secrets outside Git
- Pinned explicit official container image versions
- Deployed the Compose definition and non-secret environment through Ansible
- Validated the Compose definition locally and on the server

### Initial application stack

- Created protected WordPress and MariaDB secret files through Ansible
- Configured Nginx as the public reverse proxy
- Started Nginx, WordPress Apache and MariaDB with Docker Compose
- Verified MariaDB health and WordPress database connectivity
- Confirmed that only Nginx publishes an application port
- Confirmed that MariaDB is not published to the host
- Blocked requests for dotfiles at Nginx
- Verified persistent WordPress content survives container recreation

### Origin TLS

- Created an RSA Cloudflare Origin CA certificate for `chintavabna.com` and
  `*.chintavabna.com`
- Kept the Origin CA certificate and private key outside Git
- Deployed the certificate and private key through Ansible
- Protected the remote TLS directory and private key with restrictive
  permissions
- Configured Nginx to terminate HTTPS on TCP 443
- Redirected normal HTTP requests to HTTPS
- Kept the HTTP platform health endpoint available for local checks
- Configured WordPress to recognise HTTPS forwarded by Nginx
- Validated the Nginx configuration in a disposable container before
  recreating the running proxy
- Verified the certificate chain, validity and hostname externally using the
  Cloudflare Origin CA root
- Verified both apex and wildcard hostnames before changing production DNS
- Confirmed that public production traffic still reaches the old server

## Current architecture decisions

- Ubuntu 24.04 LTS is the managed server operating system
- Ansible manages host configuration
- Docker Compose will manage application containers
- Nginx, WordPress Apache and MariaDB will run as separate containers
- Cloudflare remains authoritative DNS and the public proxy
- The server and infrastructure logs use UTC
- Production data and secrets remain outside Git
- Production DNS remains pointed at the old server until testing passes

## Next phase

Phase 8: inspect the legacy WordPress server and export its database and
`wp-content`.

Phase 8 must not modify or interrupt the live site. The legacy server will be
inspected first so that its actual WordPress paths, database settings, service
layout, storage usage and export requirements are known before backups are
created.


## Cutover requirement

Before the Phase 10 DNS cutover, create and copy off-server a fresh MariaDB
dump and WordPress content backup. Full scheduled backup automation and
restoration testing remain Phase 11 work.

## Safety state

- Production DNS still points to the old server
- The old server has not been modified
- The new server does not receive production traffic
- MariaDB is not exposed
- UFW is active with default-deny inbound policy
- HTTP and HTTPS are temporarily public for migration testing
- Cloudflare-only origin restrictions have not been enabled
- The application stack is running on the new server
- The new origin accepts HTTPS using a Cloudflare Origin CA certificate
- External pre-DNS HTTPS testing has passed without changing production DNS