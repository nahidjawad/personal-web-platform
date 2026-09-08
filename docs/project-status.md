# Project Status

## Current phase

Phase 5 in progress: the Docker Compose application architecture has been
approved. No application containers or databases are running yet.

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

Phase 5: design and implement the initial Docker Compose application platform.

Planned work:

- Learn the Compose service, network and volume model
- Decide the repository and server directory layout
- Define explicit container image versions
- Separate frontend and backend container networks
- Create the internal Docker networks
- Create persistent storage for WordPress and MariaDB
- Create the initial environment-variable template
- Ensure MariaDB is not published to the host
- Validate the Compose configuration before starting the application

## Cutover requirement

Before the Phase 10 DNS cutover, create and copy off-server a fresh MariaDB
dump and WordPress content backup. Full scheduled backup automation and
restoration testing remain Phase 11 work.

## Safety state

- Production DNS still points to the old server
- The old server has not been modified
- The new server does not receive production traffic
- Docker is installed, but the application stack is not deployed
- No application containers or databases are currently running
- MariaDB is not exposed
- UFW is active with default-deny inbound policy
- HTTP and HTTPS are temporarily public for migration testing
- Cloudflare-only origin restrictions have not been enabled