# Project Status

## Current phase

Phase 3 complete: the Ansible-managed Ubuntu host baseline is configured
and verified.

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

## Current architecture decisions

- Ubuntu 24.04 LTS is the managed server operating system
- Ansible manages host configuration
- Docker Compose will manage application containers
- Nginx, WordPress PHP-FPM and MariaDB will run as separate containers
- Cloudflare remains authoritative DNS and the public proxy
- The server and infrastructure logs use UTC
- Production data and secrets remain outside Git
- Production DNS remains pointed at the old server until testing passes

## Next phase

Phase 4: install and verify Docker Engine and the Docker Compose plugin
using Ansible.

Planned work:

- Add Docker’s official Ubuntu package repository
- Install Docker Engine
- Install the Docker Compose and Buildx plugins
- Configure Docker logging defaults
- Enable Docker at boot
- Decide how administrative Docker access will be handled
- Verify Docker with a disposable test container
- Verify the Docker role is idempotent
- Document the Docker installation and operating model

## Safety state

- Production DNS still points to the old server
- The old server has not been modified
- The new server does not receive production traffic
- Docker and the application stack are not installed yet
- MariaDB is not exposed
- UFW is active with default-deny inbound policy
- HTTP and HTTPS are temporarily public for migration testing
- Cloudflare-only origin restrictions have not been enabled