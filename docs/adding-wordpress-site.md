# Add another WordPress site

## Scope

This is a planning and deployment runbook for a future second site. Only
Chintavabna is currently deployed and covered by the existing backup job.
Adding a second site requires its own application data, secrets, TLS,
recovery coverage and validation before public cutover.

Do not use `docker compose down --volumes` on this platform.

## Plan the site

Record the domain, expected traffic, existing files and database, required
plugins, email provider and recovery objective. Check available memory and
disk space before adding another database and WordPress container.

For an existing site, inventory its database, `wp-content`, generated root
files and configuration before exporting anything. Keep export archives and
credentials outside Git. For a new empty site, there is no import step.

## Extend the Compose stack

Create a branch and add separate services to `compose/compose.yaml`:

- A WordPress service with a distinct name, using a reviewed pinned image.
- A MariaDB service with a distinct name and health check.
- A private backend network for that WordPress/database pair.
- Separate named volumes for the WordPress root, `wp-content` and database.
- Separate file-based WordPress database and MariaDB root passwords.
- The new WordPress service joins the existing frontend network so the
  existing Nginx proxy can reach it.

Do not publish ports from the new WordPress or database containers. Only the
existing Nginx proxy publishes host ports 80 and 443. Do not reuse
Chintavabna's volumes, database account or secrets.

Extend the Ansible deployment and secret provisioning roles for the new
configuration. Validate the rendered Compose configuration before deployment.

## Configure routing and TLS

Add an Nginx virtual host for the new hostname, pointing to the new
WordPress service. Avoid a second `default_server` declaration. Deploy a
Cloudflare Origin CA certificate covering the new hostname and mount its
certificate and key read-only into the proxy. Protect the private key outside
Git. Validate Nginx configuration before recreating the proxy.

Keep the new DNS record proxied through Cloudflare with Full (strict).
The existing Lightsail web allowlist applies to the shared Nginx origin;
it does not require publishing another port. If the new domain is in a
different Cloudflare account or zone, confirm its proxy and certificate
configuration independently.

## Protect and test the data

Extend the backup job and isolated restore test to include the new site's
database dump, WordPress root files and `wp-content` volume. Give the new
site an identifiable snapshot tag or separate backup job and Healthchecks
check. Verify that a snapshot can be restored into isolated storage before
relying on it. The current Chintavabna backup does not automatically cover
another site's volumes or database.

Before changing public DNS, test the new hostname through the origin using
`curl --resolve` and the Cloudflare Origin CA trust certificate. Check the
homepage, login, administration, permalinks, uploads, plugins, database
health, email and logs. Confirm Chintavabna still works after the proxy
change.

After cutover, check the proxied public site, administration, email,
monitoring and a fresh backup. Record the deployment and recovery procedure.

## Rollback

Keep the former origin or an independently verified export until the new
site passes its monitoring window. If cutover fails, restore only that
site's proxied DNS record; leave Chintavabna and mail-related DNS records
unchanged. Preserve any writes made on the new site before reverting DNS.
Do not remove named volumes during rollback.