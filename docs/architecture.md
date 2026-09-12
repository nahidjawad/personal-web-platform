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
    wproot[("WordPress root")]
    wpcontent[("WordPress content")]
    dbdata[("MariaDB data")]
    backup["Off-server backup storage"]

    visitor --> cloudflare
    cloudflare --> lightsail
    lightsail --> nginx
    nginx --> wordpress
    wordpress --> mariadb
    wordpress --> wproot
    wordpress --> wpcontent
    mariadb --> dbdata
    wpcontent --> backup
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

Production traffic reaches the new Lightsail server through Cloudflare.

Cloudflare provides authoritative DNS, public TLS and reverse proxying.
Cloudflare validates the new origin using Full (strict) mode and the installed
Origin CA certificate. Nginx terminates origin TLS and proxies application
requests to WordPress Apache.

The migrated WordPress database and content are now live. Public application,
administration and email-delivery testing passed after cutover.

The legacy server remains available as the temporary rollback origin and still
contains two unrelated inactive or unfinished workloads. Those workloads must
be archived, migrated or deliberately discarded before the legacy server is
deleted.

## Network exposure

The production host currently permits:

- TCP 22 for rate-limited SSH
- TCP 80 for pre-cutover HTTP testing
- TCP 443 for pre-cutover HTTPS testing

MariaDB will not be exposed on a host or public port.

After production verification, HTTP and HTTPS origin access will be
restricted to Cloudflare address ranges. SSH will remain independently
controlled.

## Persistence model

Containers are disposable. The following named volumes preserve application
state:

- `wordpress_root` for the WordPress document root, generated configuration,
  `.htaccess` and root-level generated files
- `wordpress_data` for plugins, themes, uploads and other `wp-content`
- `mariadb_data` for MariaDB database files

The separate WordPress root and content mounts make all persistent application
storage explicit while allowing `wp-content` to be backed up independently.

Production environment configuration and TLS material remain on the host
outside Git. Database files, uploads, secrets and backup archives are also
excluded from Git.