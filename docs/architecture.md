# Platform Architecture

## Purpose

The Personal Web Platform is a reproducible, container-based hosting
environment for small public web applications.

The initial workload is `chintavabna.com`. The platform is designed to
accommodate additional low-traffic applications later without coupling
the server configuration to one website.

## Target runtime architecture

```mermaid
flowchart TD
    visitor["Visitor or administrator"]
    cloudflare["Cloudflare<br/>DNS, CDN, proxy and public TLS"]
    lightsail["AWS Lightsail<br/>Ubuntu 24.04 LTS"]
    nginx["Nginx container<br/>Origin TLS and routing"]
    wordpress["WordPress Apache container"]
    mariadb["MariaDB container"]
    wpdata[("WordPress data")]
    dbdata[("MariaDB data")]
    backup["Off-server backup storage"]

    visitor --> cloudflare
    cloudflare --> lightsail
    lightsail --> nginx
    nginx --> wordpress
    wordpress --> mariadb
    wordpress --> wpdata
    mariadb --> dbdata
    wpdata --> backup
    dbdata --> backup
```

## Provisioning workflow

```mermaid
flowchart LR
    engineer["Administrator"]
    repo["GitHub repository"]
    controller["WSL Ansible controller"]
    server["Lightsail server"]
    compose["Docker Compose"]

    engineer --> repo
    repo --> controller
    controller -->|SSH| server
    server --> compose
```

## Responsibility boundaries

| Component | Responsibility |
|---|---|
| Cloudflare | Authoritative DNS, public TLS, proxying, caching and edge security |
| Lightsail firewall | AWS network-level ingress control |
| UFW | Host-level ingress policy and SSH rate limiting |
| Ansible | Reproducible host configuration |
| Docker Compose | Application-container lifecycle |
| Nginx | Reverse proxy, origin TLS and virtual-host routing |
| WordPress/Apache | WordPress, PHP and application HTTP handling |
| MariaDB | Persistent WordPress relational data |
| Named volumes | Persistent application and database storage |
| Backup system | Recovery copies stored independently of the VPS |

## Current deployment state

Production traffic still reaches the old server through Cloudflare.

The new server is not yet a production origin. It currently contains the
secured Ubuntu host baseline and the Ansible-managed Docker platform.
Nginx, WordPress Apache and MariaDB are running under Docker Compose. The
database is healthy, application traffic reaches WordPress through Nginx, and
persistent WordPress content survives container recreation.

Nginx now terminates HTTPS using a Cloudflare Origin CA certificate covering
`chintavabna.com` and `*.chintavabna.com`. The certificate and private key are
stored outside Git and mounted read-only into the Nginx container. External
pre-DNS testing has verified the certificate chain, hostname coverage, HTTP
redirect and HTTPS health endpoint.

## Network exposure

The initial host permits:

- TCP 22 for rate-limited SSH
- TCP 80 for pre-cutover HTTP testing
- TCP 443 for pre-cutover HTTPS testing

MariaDB will not be exposed on a host or public port.

After production verification, HTTP and HTTPS origin access will be
restricted to Cloudflare address ranges. SSH will remain independently
controlled.

## Persistence model

Containers are disposable. The following state must survive container
replacement:

- MariaDB database files
- WordPress content and uploads
- production environment configuration
- TLS certificate and private key
- backup and operational state

Secrets, database files, uploads and backup archives are excluded from Git.