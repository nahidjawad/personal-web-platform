# Engineering Decisions

This document records why major platform choices were made. It prevents
future rebuilds from repeating the same research without context.

## Decision summary

| Decision | Selected option | Reason |
|---|---|---|
| AWS region | Mumbai | Primary readership is in Bangladesh and the existing workload is already nearby |
| Instance size | 4 GB RAM, 2 vCPU, 80 GB SSD | Provides safer memory headroom than the previous 2 GB server |
| Operating system | Ubuntu 24.04 LTS | Supported Docker path, broad Ansible support and portability across VPS providers |
| Provisioning | Ansible over SSH | Makes host configuration repeatable and reviewable |
| Controller | WSL 2 with isolated Python 3.12 | Keeps automation tooling separate from Windows and other projects |
| Application runtime | Docker Compose | Provides understandable, reproducible container orchestration for a single VPS |
| Web stack | Nginx and WordPress PHP-FPM | Provides explicit routing, FastCGI and origin TLS configuration |
| Database | MariaDB container | Maintains WordPress compatibility while isolating the database from the host |
| Server timezone | UTC | Keeps infrastructure, Cloudflare and application logs consistently comparable |
| Swap | 2 GiB with swappiness 10 | Provides emergency memory protection without encouraging normal swap use |
| Host firewall | UFW | Gives Ubuntu-native, readable and Ansible-managed host policy |
| Public edge | Cloudflare | Retains existing authoritative DNS, proxy, CDN and public TLS |
| Origin TLS | Cloudflare Origin CA | Authenticates and encrypts Cloudflare-to-origin traffic |
| Secrets | Stored outside Git | Prevents credentials, private keys and production state entering repository history |

## Why Ubuntu instead of Amazon Linux

Amazon Linux 2023 is a capable AWS-focused RPM-based distribution.
Ubuntu 24.04 LTS was selected because this platform should be portable
to another Lightsail instance or a different VPS provider.

Docker publishes a direct supported installation path for Ubuntu, and
Ubuntu has broad support across Ansible roles and operational examples.

## Why Ansible and Docker Compose are both used

They manage different layers:

- Ansible configures the server.
- Docker Compose runs the application stack.

Ansible installs Docker, creates directories, deploys configuration and
can invoke Compose. Compose defines containers, networks, volumes and
runtime relationships.

## Why the server remains on UTC

Infrastructure timestamps should be unambiguous and comparable across
systems. WordPress can independently display dates using its configured
application timezone.

## Why firewalling exists at multiple layers

Lightsail firewall rules protect the AWS network boundary. UFW protects
the operating-system host.

Docker-published ports can interact with packet filtering outside UFW's
normal rules. Cloudflare-only origin restrictions will therefore account
for Lightsail rules and Docker's networking behaviour rather than relying
on UFW alone.