# Security Controls

## Current controls

- Lightsail permits inbound TCP 22, 80 and 443
- UFW defaults to denying inbound traffic and rate-limits SSH
- Docker administration requires `sudo`
- Only Nginx publishes an application port
- MariaDB is reachable only through the private Compose backend network
- Production secrets and persistent data are excluded from Git
- Nginx denies requests for dotfiles
- Cloudflare-to-origin traffic is encrypted using a Cloudflare Origin CA
  certificate
- Nginx terminates origin TLS on TCP 443
- The Origin CA private key is root-owned, mode 0600 and excluded from Git
- TLS files are mounted read-only into the Nginx container
- Cloudflare uses Full (strict) validation for origin HTTPS
- Public WordPress email uses Amazon SES with verified SPF, DKIM and DMARC
- Restic encrypts WordPress backups before uploading to Cloudflare R2
- The R2 access keys, repository password and Healthchecks URLs are held in root-owned files outside Git
- Daily backup and weekly maintenance report to separate Healthchecks checks

## Application secrets

The `.env` file contains non-secret configuration such as the database name
and username. Passwords are stored separately under:

```bash
/srv/personal-web-platform/secrets
```
The WordPress database password is root-owned, readable by the www-data
group, and mode 0640. The MariaDB root password is root-owned and mode
0600. Compose mounts these files read-only into their containers.

Create missing secret files with:
```bash
cd ansible
uv run ansible-playbook playbooks/application-secrets.yml
```
The playbook preserves existing secret values. Changing a secret file alone
does not rotate the corresponding MariaDB account password.

Cloudflare-only HTTP and HTTPS origin restrictions and the final security
review remain Phase 12 work.

For backup access and recovery procedures, see [Backups and recovery](backups.md).