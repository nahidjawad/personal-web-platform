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

## Public origin firewall

The Lightsail IPv4 firewall is the enforcement point for public TCP 80 and
443. Both ports accept only the ranges in
`config/cloudflare-ips-v4.txt`, copied from
[Cloudflare's published source](https://www.cloudflare.com/ips-v4).
The instance's public IPv6 networking is disabled in Lightsail. TCP 22 has
its own IPv4 rule and is not coupled to the web allowlist.

Docker publishes the proxy's ports on the host. Published container traffic
can bypass UFW's INPUT rules, so UFW alone must not be treated as protection
for these ports. The security role removes its old unrestricted UFW web
permissions; the Lightsail firewall protects the *public IPv4* path. The
Lightsail firewall does not filter traffic to the host's private IPv4 address
from eligible AWS/Lightsail networks. Keep that boundary in mind before
adding a peered network or another private workload.

To update the allowlist, compare the tracked text file to
[Cloudflare's live IPv4 list](https://www.cloudflare.com/ips-v4). Cloudflare
publishes additions before using them. On a change, add new prefixes to the
file, apply and verify public health first; remove obsolete prefixes only
after verification. Run the reviewed script from AWS CloudShell in
`ap-south-1` with no permanent AWS keys:

```bash
python3 scripts/lightsail-cloudflare-origin.py plan
python3 scripts/lightsail-cloudflare-origin.py apply
```

The script refuses unrecognized port states, preserves IPv4 SSH 22, and
prints the complete desired rule set before a write. Confirm the AWS rule
state and test the public and direct paths afterward. Its `rollback` action
reopens IPv4 web access while preserving SSH:

```bash
python3 scripts/lightsail-cloudflare-origin.py rollback
```

The CloudShell copy of the repository is temporary; review the corresponding
Git revision and current Cloudflare ranges before each application. Do not
enable public IPv6 without designing the IPv6 firewall rules first.

For backup access and recovery procedures, see [Backups and recovery](backups.md).
