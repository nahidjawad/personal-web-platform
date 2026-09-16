# Backups and recovery

## What is protected

The daily job exports the Chintavabna MariaDB database as a compressed SQL
dump, copies generated WordPress root files, and backs up the persistent
`wordpress_data` volume (plugins, themes and uploads). Restic encrypts the
snapshot locally before sending it to the Cloudflare R2 bucket. The live
MariaDB data directory is not copied: the logical dump is the database
recovery artifact.

The database export uses `mariadb-dump --single-transaction`, checks the gzip
archive and requires at least one table before the snapshot is uploaded. The
WordPress files are read while the site is live; concurrent uploads or changes
can fall on either side of a snapshot. For strict point-in-time consistency,
pause writes during a separately planned recovery point.

| Component | Schedule (UTC) | Purpose |
|---|---|---|
| `personal-web-backup.timer` | Daily at 18:30, up to 30 minutes of random delay | Export and upload a snapshot; apply retention without pruning |
| `personal-web-backup-maintenance.timer` | Sunday at 20:00, up to 30 minutes of random delay | Apply retention with pruning, read-check 5% of repository data, clean local cache |

Both timers have `Persistent=true`: systemd starts a missed run after the
server comes back. Both jobs share a lock to avoid running concurrently.
The backup policy retains 7 daily, 4 weekly and 6 monthly snapshots, selected
by the `chintavabna` tag. The value `personal-web-prod-01` is used as the
stable host label for new snapshots; older snapshots with the former host
label remain eligible for listing, retention and restoration by tag.

## Secrets and monitoring

Run from the controller's `ansible` directory. Provision the Restic/R2
credentials on a new host once with:

```bash
uv run ansible-playbook playbooks/backup-secrets.yml
```

The playbook creates root-owned secret files under
`/srv/personal-web-platform/secrets/backup`. Existing files are preserved by
default. Do not regenerate the Restic repository password on a replacement
host: recover the *original* password from a separate protected copy. Losing
it makes the encrypted backups unreadable.

Provision the separate Healthchecks.io ping URLs with:

```bash
uv run ansible-playbook playbooks/backup-monitoring-secrets.yml
```

The two URL files are root-owned and mode `0600`. The daily check is scheduled
for 18:30 UTC with a 45-minute grace period; the weekly check is scheduled
for Sunday 20:00 UTC with a 90-minute grace period. The scripts send `/start`,
then success or `/fail`; ping failures are logged without changing the
backup job's result. UptimeRobot continues to check site availability, which
does not prove that a backup exists. If normal runs begin taking longer than
their grace periods, adjust the Healthchecks configuration.

Deploy the role after provisioning the secrets:

```bash
uv run ansible-playbook playbooks/backups.yml
```

The role verifies access to the existing repository and fails if it cannot
read it. Repository initialization is an explicit option for a genuinely
empty new bucket; routine deployments leave `backup_repository_initialize`
false. Secret provisioning does not perform credential rotation.

## Inspect and run

From the controller's `ansible` directory, inspect the timers:

```bash
uv run ansible web_servers --become --module-name ansible.builtin.command \
  --args="systemctl list-timers --all personal-web-backup.timer personal-web-backup-maintenance.timer"
```

Start a backup on demand and inspect its recorded result:

```bash
uv run ansible web_servers --become --module-name ansible.builtin.command \
  --args="systemctl start personal-web-backup.service"
uv run ansible web_servers --become --module-name ansible.builtin.command \
  --args="systemctl show personal-web-backup.service --property=Result --property=ExecMainStatus"
uv run ansible web_servers --become --module-name ansible.builtin.command \
  --args="journalctl --unit personal-web-backup.service --lines=35 --no-pager"
```

`Result=success` and `ExecMainStatus=0` show a successful run. The completed
one-shot service normally reports `inactive (dead)`; `systemctl status`
itself may return 3 in that state. Confirm the new snapshot in Restic and
the daily check's latest success in Healthchecks.io.

Run weekly maintenance manually only when needed:

```bash
uv run ansible web_servers --become --module-name ansible.builtin.command \
  --args="systemctl start personal-web-backup-maintenance.service"
uv run ansible web_servers --become --module-name ansible.builtin.command \
  --args="systemctl show personal-web-backup-maintenance.service --property=Result --property=ExecMainStatus"
```

Maintenance includes pruning and can take longer as the repository grows.
Inspect its journal before diagnosing a failed or overdue weekly check.

## Verify a restoration

The restore-test script restores one snapshot into temporary storage, checks
the database dump and WordPress files, imports the dump into a disposable
MariaDB container on an isolated Docker network, compares table counts, and
removes its temporary container, volume and files on exit. It does not write
to the running production database or WordPress volumes.

Run it against the newest tagged snapshot from the controller:

```bash
uv run ansible web_servers --become --module-name ansible.builtin.command \
  --args="/usr/local/sbin/personal-web-restore-test latest"
```

Expect `Isolated restore test passed` and the database table count. To test a
specific snapshot, supply its Restic ID in place of `latest`. Ensure the
server has enough free disk space for the restored files and temporary
MariaDB volume before starting. Repeat an isolated restoration periodically,
especially after changing the backup job or WordPress storage layout.

## Recover the live site

The isolated test proves that the saved files can be read and the SQL dump
can be imported. The procedure below is for a **new, empty replacement host**.
It has not been exercised end to end on a replacement host. Do not run its
volume creation or database import commands on the current production host.
It is a manual recovery runbook; the scheduled backup and isolated restore
test are scripted.

### 1. Gather access and choose a snapshot

You need the Git repository, SSH access to a new Ubuntu 24.04 Lightsail
instance, access to Cloudflare DNS, and the following protected materials
from a separate location:

- The **original Restic repository password** and an R2 key with access to
  the existing bucket (read access for restore; scoped write access for later
  backups); a newly invented password cannot decrypt snapshots.
- WordPress database and MariaDB root passwords for the replacement host.
  Reuse the saved originals when possible. The existing `wp-config.php` must
  agree with the database credentials.
- The Cloudflare Origin CA certificate and matching private key, or a newly
  issued certificate and key for this hostname.

Choose a recovery point based on its time. Newer writes after that snapshot
will be missing. If the old host is still available, stop WordPress writes or
put it into maintenance mode and take one last backup before switching hosts.
Record the chosen snapshot ID and both old and new origin addresses privately.
Do not change Cloudflare DNS yet.

### 2. Rebuild the host with Ansible

Create a new Lightsail instance and static IP in the intended region. Permit
SSH from your administration location and HTTP/HTTPS according to the current
firewall policy. On the controller, check out the reviewed Git revision,
create a fresh ignored `ansible/inventories/production/hosts.yml` pointing to
the **new** IP, and verify Ansible connectivity. Follow
[Deployment](deployment.md) for the controller and inventory setup.

From the controller's `ansible` directory, apply the host and platform
playbooks to the replacement host:

```bash
uv run ansible-playbook playbooks/preflight.yml
uv run ansible-playbook playbooks/baseline.yml
uv run ansible-playbook playbooks/reboot-if-required.yml
uv run ansible-playbook playbooks/swap.yml
uv run ansible-playbook playbooks/security.yml
uv run ansible-playbook playbooks/docker.yml
uv run ansible-playbook playbooks/compose-platform.yml
uv run ansible-playbook playbooks/application-secrets.yml
uv run ansible-playbook playbooks/origin-tls.yml
```

Supply the saved application passwords and TLS file paths at the prompts.
The application secrets playbook preserves existing files, so verify the
inventory targets only the replacement host before running it. Do not start
WordPress or the proxy yet.

Provision Restic credentials with `backup-secrets.yml` on the replacement
host. Enter the existing repository password, the R2 endpoint and access
key. Its `restic.env` must point to the original R2 bucket. You may use a
new, appropriately scoped R2 access key; the Restic password must match the
repository. Provision the two monitoring URLs separately with
`backup-monitoring-secrets.yml`, but deploy `backups.yml` only **after** the
site has been restored so persistent timers cannot back up an empty site.

### 3. Restore encrypted data to a staging directory

Open a root Bash session on the **replacement host**. The commands below
assume this shell; `RECOVERY_ROOT` and `RECOVERY_SNAPSHOT` exist only here:

```bash
sudo -i
set -euo pipefail
set -a
. /srv/personal-web-platform/secrets/backup/restic.env
set +a
restic snapshots --tag chintavabna --compact
```

Set the selected ID, then restore to protected temporary storage:

```bash
RECOVERY_SNAPSHOT=c57ff539  # Replace with the selected snapshot ID
RECOVERY_ROOT=/var/lib/personal-web-platform-backup/recovery
install -d -m 0700 "$RECOVERY_ROOT"
restic restore "$RECOVERY_SNAPSHOT" --tag chintavabna --target "$RECOVERY_ROOT"
RECOVERY_SQL="$RECOVERY_ROOT/var/lib/personal-web-platform-backup/current/database/chintavabna.sql.gz"
RECOVERY_WP_ROOT="$RECOVERY_ROOT/var/lib/personal-web-platform-backup/current/wordpress-root"
RECOVERY_WP_DATA="$RECOVERY_ROOT/var/lib/docker/volumes/personal-web-platform_wordpress_data/_data"
gzip -t "$RECOVERY_SQL"
test -s "$RECOVERY_WP_ROOT/wp-config.php"
test -d "$RECOVERY_WP_DATA/uploads"
```

Ensure there is enough free disk space before the restore. The database dump
and WordPress files contain private data; retain root-only permissions on the
staging directory. Do not assume that `latest` is the desired recovery point.

### 4. Populate the new database and WordPress volumes

Start MariaDB alone. Compose initializes a fresh database and account using
the supplied application secrets:

```bash
cd /srv/personal-web-platform
docker compose --env-file .env pull
docker compose --env-file .env up --detach --wait database
docker compose --env-file .env ps
```

Import the saved logical dump through the private database container. The
password is read inside the container from its mounted secret file:

```bash
gzip -dc "$RECOVERY_SQL" | docker compose --env-file .env exec -T database \
  sh -c 'MYSQL_PWD="$(cat /run/secrets/mariadb_root_password)" \
    exec mariadb --user=root "$MARIADB_DATABASE"'
docker compose --env-file .env exec -T database sh -c \
  'MYSQL_PWD="$(cat /run/secrets/mariadb_root_password)" \
    exec mariadb --user=root --batch --skip-column-names \
    "$MARIADB_DATABASE" --execute="SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE()"'
```

The returned table count was 43 for the snapshot tested on 2026-09-16;
compare against the table count of the snapshot you actually selected.
MariaDB data is rebuilt from the SQL dump. Do not copy database data files
from another running host.

Create the two WordPress volumes with the names expected by Compose. The
WordPress image will install its pinned core files into the root volume when
it first starts; the backup supplies generated root files and `wp-content`:

```bash
docker volume create personal-web-platform_wordpress_root
docker volume create personal-web-platform_wordpress_data
docker run --rm --network none --entrypoint sh \
  --mount "type=bind,source=$RECOVERY_WP_ROOT,target=/restore,readonly" \
  --mount type=volume,source=personal-web-platform_wordpress_root,target=/target \
  wordpress:7.1.0-php8.3-apache -c 'cp -a /restore/. /target/'
docker run --rm --network none --entrypoint sh \
  --mount "type=bind,source=$RECOVERY_WP_DATA,target=/restore,readonly" \
  --mount type=volume,source=personal-web-platform_wordpress_data,target=/target \
  wordpress:7.1.0-php8.3-apache -c 'cp -a /restore/. /target/'
```

These copy commands use a disposable container and preserve file ownership.
Confirm the restored `wp-config.php` reads the replacement host's WordPress
database settings before starting WordPress. If it contains literal old
credentials, reconcile them without exposing passwords in terminal output.

### 5. Start, verify and redirect traffic

With the origin TLS files already deployed, start WordPress and the proxy:

```bash
docker compose --env-file .env up --detach --wait wordpress proxy
docker compose --env-file .env ps
docker compose --env-file .env exec proxy nginx -t
curl --fail http://127.0.0.1/platform-health
```

Confirm the database is healthy, all three containers run, the homepage and
`/books/` return expected content, uploads load, and WordPress administration
works. Test the new origin privately before updating public DNS. An Origin
CA certificate will not be trusted by a normal browser connecting directly;
use the Cloudflare Origin CA trust chain for direct TLS verification. Verify
the WordPress mail path, plugins and logs as well.

For example, from the controller, replace both placeholders below with the
new static IP and the local Cloudflare Origin CA root certificate file:

```bash
curl --fail --show-error \
  --resolve chintavabna.com:443:NEW_STATIC_IP \
  --cacert /path/to/cloudflare-origin-ca-root.pem \
  https://chintavabna.com/books/
```

Update only the proxied apex A record in Cloudflare to the new static IP;
keep the `www` CNAME and mail records. With Full (strict) enabled, verify
the public site and `/platform-health` through Cloudflare and send a test
email. If the old host still exists, stop its backup timers to avoid two
machines writing snapshots for the same site. Keep the old host until the
new site passes a monitoring window and the separate legacy workloads have
been handled as described in [Project status](project-status.md).

Return to the WSL Ansible controller, verify that its inventory points to the replacement host, and run from the repository’s ansible directory:

```bash
uv run ansible-playbook playbooks/backups.yml
```

Run a new backup, check its Healthchecks ping, and run the isolated restore
test against that new snapshot. Use the inspection commands earlier in this
guide. Once recovery has been accepted, remove the protected staging tree
from the replacement host and confirm its free disk space. Keep the original
Restic password and R2 access recovery path documented outside this repo.
