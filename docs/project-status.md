# Project Status

## Current phase

Phase 10 complete: Cloudflare production traffic was switched to the new
container platform, public application and email delivery tests passed, and
initial monitoring found no relevant errors.

## Overall completion

83% complete: 10 of 12 phases have passed verification.

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

### Compose platform foundation

- Created the application deployment directories through Ansible
- Set `/srv/personal-web-platform` as the deployment root
- Created the Nginx configuration directories
- Restricted the secrets directory to root
- Confirmed the Compose platform role is idempotent
- Defined Nginx, WordPress Apache and MariaDB services
- Separated frontend and private backend container networks
- Defined persistent WordPress and MariaDB named volumes
- Configured file-based secrets outside Git
- Pinned explicit official container image versions
- Deployed the Compose definition and non-secret environment through Ansible
- Validated the Compose definition locally and on the server

### Initial application stack

- Created protected WordPress and MariaDB secret files through Ansible
- Configured Nginx as the public reverse proxy
- Started Nginx, WordPress Apache and MariaDB with Docker Compose
- Verified MariaDB health and WordPress database connectivity
- Confirmed that only Nginx publishes an application port
- Confirmed that MariaDB is not published to the host
- Blocked requests for dotfiles at Nginx
- Verified persistent WordPress content survives container recreation

### Origin TLS

- Created an RSA Cloudflare Origin CA certificate for `chintavabna.com` and
  `*.chintavabna.com`
- Kept the Origin CA certificate and private key outside Git
- Deployed the certificate and private key through Ansible
- Protected the remote TLS directory and private key with restrictive
  permissions
- Configured Nginx to terminate HTTPS on TCP 443
- Redirected normal HTTP requests to HTTPS
- Kept the HTTP platform health endpoint available for local checks
- Configured WordPress to recognise HTTPS forwarded by Nginx
- Validated the Nginx configuration in a disposable container before
  recreating the running proxy
- Verified the certificate chain, validity and hostname externally using the
  Cloudflare Origin CA root
- Verified both apex and wildcard hostnames before changing production DNS
- Confirmed that public production traffic still reaches the old server

### Legacy inspection and initial export

- Confirmed the legacy WordPress document root and external configuration
  arrangement
- Confirmed the site-level configuration loads a protected shared
  configuration outside the document root
- Recorded the legacy Nginx, PHP-FPM, WordPress and MariaDB layout
- Confirmed all 39 WordPress database tables use InnoDB
- Created a consistent online logical database dump without stopping
  production
- Created a complete archive of `wp-content`
- Confirmed the active Magbook theme and custom book-recommendations plugin
  are present in the archive
- Preserved the custom `robots.txt` separately
- Generated SHA-256 checksums for all migration artifacts
- Copied the export off the legacy server
- Verified all checksums and compressed archives after transfer
- Confirmed production remained available throughout the export

### WordPress migration and pre-cutover backup

- Transferred the verified Phase 8 migration artifacts to the new server
- Verified source checksums again after transfer
- Replaced the placeholder WordPress database and `wp-content`
- Preserved the active theme, custom plugin, uploads and application data
- Confirmed all imported database tables use the expected prefix
- Disabled automatic WordPress core updates because core releases are managed
  through the pinned container image
- Kept dashboard-based plugin and theme management available
- Verified the homepage, login, administration, REST API, books and content
  routes through pre-DNS HTTPS testing
- Verified WordPress can write to persistent content storage
- Confirmed no relevant fatal, database, permission or upstream errors
- Made the WordPress document root and `wp-content` explicit named volumes
- Verified generated root files and custom content survive container recreation
- Created fresh MariaDB, `wp-content` and generated-file backups
- Copied the fresh backups off-server and verified their SHA-256 checksums

### Production cutover

- Confirmed the old and new origin details were available for rollback
- Changed Cloudflare SSL/TLS mode from Full to Full (strict)
- Verified the legacy origin certificate before enabling strict validation
- Changed only the proxied apex A record to the new Lightsail static IP
- Preserved the proxied `www` CNAME and all email-related DNS records
- Verified `/platform-health` changed from the old-origin 404 response to the
  new-origin HTTP 200 response
- Confirmed both apex and `www` hostnames work through Cloudflare
- Confirmed `www` redirects to the canonical apex hostname
- Verified public WordPress pages, administration, REST API and generated SEO
  files
- Confirmed new public requests appeared in the Nginx container logs
- Sent and received a WordPress test email through Amazon SES
- Confirmed SPF, DKIM and DMARC authentication passed
- Checked container state, host resources and logs after cutover
- Found no relevant application, database, permission, upstream or HTTP 5xx
  errors

## Current architecture decisions

- Ubuntu 24.04 LTS is the managed server operating system
- Ansible manages host configuration
- Docker Compose manages application containers
- Nginx, WordPress Apache and MariaDB run as separate containers
- Cloudflare is authoritative DNS, the public proxy and the public TLS endpoint
- Cloudflare uses Full (strict) validation for the HTTPS origin connection
- WordPress core versions are managed through the pinned container image
- Production data and secrets remain outside Git
- The server and infrastructure logs use UTC

## Next phase

Phase 11: implement automated MariaDB and `wp-content` backups, off-server
storage, retention, failure notification and a verified restoration test.

## Old-server retirement decision

The legacy server remains unchanged for a minimum 24-hour Chintavabna
post-cutover rollback window.

The server also contains two unrelated inactive or unfinished workloads.
Before deleting the legacy server, those workloads must be inspected and
either archived off-server, migrated or deliberately discarded.

The legacy server may be deleted only after:

- the Chintavabna monitoring window passes
- the new platform remains healthy
- the verified Phase 8 and Phase 9 backups remain available
- the remaining legacy workloads have been preserved or deliberately discarded

Stopping a Lightsail instance does not replace deletion as a long-term
cost-control measure.

## Safety state

- Production traffic reaches the new server through Cloudflare
- Cloudflare SSL/TLS mode is Full (strict)
- The proxied apex record targets the new Lightsail static IP
- The proxied `www` record remains a CNAME to the apex
- MariaDB is not published to the host
- UFW is active with a default-deny inbound policy
- HTTP and HTTPS remain temporarily reachable at the origin
- Cloudflare-only origin restrictions remain Phase 12 work
- The Phase 8 migration export remains stored off-server
- The Phase 9 pre-cutover recovery checkpoint remains stored off-server
- The old server remains available temporarily for rollback
- Scheduled backups and restoration testing remain Phase 11 work
- Two unrelated legacy workloads still require preservation or an explicit
  discard decision before the old server can be deleted