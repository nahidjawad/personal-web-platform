# Project Status

## Current phase

Phase 2 complete: Ansible controller and SSH connectivity established.

## Completed

- Created AWS Lightsail instance `personal-web-prod-01`
- Selected Mumbai region
- Selected Ubuntu 24.04 LTS OS-only blueprint
- Selected 4 GB RAM, 2 vCPU and 80 GB SSD plan
- Attached a static IPv4 address
- Configured initial Lightsail firewall for TCP ports 22, 80 and 443
- Verified Ubuntu, CPU, memory and disk capacity
- Installed `uv` in WSL
- Pinned controller Python to 3.12
- Installed Ansible Core and Ansible Lint
- Created local production and safe example inventories
- Secured the Lightsail SSH key outside the repository
- Verified SSH host identity
- Verified Ansible connectivity with `ansible.builtin.ping`

## Current architecture decisions

- Ubuntu 24.04 LTS is the managed server operating system
- Ansible manages host configuration
- Docker Compose manages application containers
- Nginx, WordPress PHP-FPM and MariaDB run as separate containers
- Cloudflare remains authoritative DNS and the public proxy
- Production data and secrets remain outside Git
- Production DNS remains pointed at the old server until testing passes

## Next phase

Phase 3: create and apply the Ansible host baseline.

Planned work:

- Record the untouched server baseline
- Update operating-system packages
- Set hostname and timezone
- Install baseline administration packages
- Configure swap
- Configure UFW without losing SSH access
- Create platform directories
- Configure basic host logging
- Verify idempotency

## Safety state

- Production DNS has not been changed
- The old server has not been modified
- The new server does not yet host application traffic
- HTTP and HTTPS origin lockdown has not been enabled