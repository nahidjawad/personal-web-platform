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
    wordpress["WordPress PHP-FPM container"]
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