# Personal Web Platform

A reproducible, container-based platform for hosting personal web applications on AWS Lightsail.

The platform initially hosts `chintavabna.com`. It is designed to support additional applications later without coupling the infrastructure repository to one website.

## Planned architecture

- AWS Lightsail
- Ubuntu 24.04 LTS
- Ansible
- Docker Engine and Docker Compose
- Nginx
- WordPress with Apache
- MariaDB
- Cloudflare DNS, proxy and origin TLS
- AWS SES for WordPress email
- Off-server backups

## Repository purpose

This repository contains:

- Ansible configuration and playbooks
- Docker Compose configuration
- Nginx configuration
- Backup and monitoring scripts
- Deployment and disaster-recovery documentation

It does not contain:

- Production secrets
- SSH private keys
- TLS private keys
- WordPress uploads
- Database contents
- Backup archives

## Current status

See [docs/project-status.md](docs/project-status.md).

## Documentation

- [Architecture](docs/architecture.md)
- [Engineering decisions](docs/decisions.md)
- [Deployment guide](docs/deployment.md)
- [Operations guide](docs/operations.md)
- [Current project status](docs/project-status.md)
- [Security controls](docs/security.md)

Migration, security and disaster-recovery documentation will be expanded as
the corresponding procedures are implemented and verified.
