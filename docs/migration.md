# WordPress Migration

## Scope

This guide records the verified process used to migrate a legacy WordPress
site to the container-based platform.

Production data, server addresses, credentials, export archives, checksum
values and environment-specific paths remain outside Git.

## Legacy platform inspection

The legacy production platform was inspected before creating exports.

| Component | Verified state |
|---|---|
| WordPress | Current production installation |
| Web path | Nginx to PHP-FPM |
| Database | Legacy MariaDB to MariaDB 11.4 migration |
| Database tables | 39 |
| Database storage engine | InnoDB |
| Database size | Approximately 41 MiB |
| WordPress installation size | Approximately 1.6 GiB |
| `wp-content` size | Approximately 1.5 GiB |
| `wp-content` symlinks | None |

The legacy site used a small document-root `wp-config.php` loader to load its
actual configuration from outside the public document root.

Neither configuration file is migrated. The new WordPress container generates
its configuration and reads database credentials from protected Docker secret
files.

The active theme and custom site plugin were confirmed under `wp-content` and
inside the completed archive.

## Set environment-specific values

Set these values privately for the source environment:

```bash
LEGACY_WP_ROOT=/path/to/wordpress
LEGACY_DB_NAME=wordpress_database
LEGACY_DB_USER=wordpress_database_user
EXPORT_TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
EXPORT_DIR="/var/backups/wordpress-migration/${EXPORT_TIMESTAMP}"
```

Do not commit the real values.

## Initial database export

Create a protected export directory:

```bash
sudo install -d \
  -o root \
  -g root \
  -m 0700 \
  "$EXPORT_DIR"
```

Create a consistent online dump of the InnoDB WordPress database:

```bash
sudo mysqldump \
  --user="$LEGACY_DB_USER" \
  --password \
  --host=localhost \
  --single-transaction \
  --quick \
  --skip-lock-tables \
  --default-character-set=utf8 \
  --hex-blob \
  "$LEGACY_DB_NAME" \
  > "$EXPORT_DIR/wordpress.sql"
```

The password is entered interactively and is not stored in shell history.

The dump intentionally omits `--databases`. This allows it to be imported into
a differently named target database without selecting or creating the legacy
database name.

Validate the dump:

```bash
sudo test -s "$EXPORT_DIR/wordpress.sql"
sudo tail -n 5 "$EXPORT_DIR/wordpress.sql"
sudo grep -c '^CREATE TABLE' "$EXPORT_DIR/wordpress.sql"
```

The verified export contained the expected 39 `CREATE TABLE` statements and
ended with the dump-completion marker.

Compress and test it:

```bash
sudo gzip "$EXPORT_DIR/wordpress.sql"
sudo gzip --test "$EXPORT_DIR/wordpress.sql.gz"
```

## Initial WordPress content export

Create the `wp-content` archive:

```bash
sudo tar \
  --create \
  --gzip \
  --file "$EXPORT_DIR/wordpress-wp-content.tar.gz" \
  --directory "$LEGACY_WP_ROOT" \
  --acls \
  --xattrs \
  --selinux \
  wp-content
```

If the site has a custom static `robots.txt`, preserve it separately:

```bash
sudo install \
  -o root \
  -g root \
  -m 0600 \
  "$LEGACY_WP_ROOT/robots.txt" \
  "$EXPORT_DIR/robots.txt"
```

Validate the archive:

```bash
sudo gzip --test "$EXPORT_DIR/wordpress-wp-content.tar.gz"

sudo tar \
  --list \
  --gzip \
  --file "$EXPORT_DIR/wordpress-wp-content.tar.gz" |
wc -l
```

The verified archive contained approximately 23,000 entries. The active theme
and custom site plugin were explicitly confirmed in the archive.

## Files intentionally excluded

The initial export does not copy:

- WordPress core, because the official container supplies it
- Legacy `wp-config.php` files
- Database credentials or authentication salts
- Legacy TLS private keys
- Old SQL exports or backup logs stored under the document root
- Generated cache-specific Nginx configuration
- Generated SEO and LLM-discovery files that the application can recreate

The legacy Nginx configuration is not directly portable to the new
Nginx-to-WordPress-Apache architecture.

## Checksums

Generate checksums after creating the export:

```bash
sudo sha256sum \
  "$EXPORT_DIR/wordpress.sql.gz" \
  "$EXPORT_DIR/wordpress-wp-content.tar.gz" \
  "$EXPORT_DIR/robots.txt" |
sudo tee "$EXPORT_DIR/SHA256SUMS"
```

Protect the export:

```bash
sudo chown -R root:root "$EXPORT_DIR"
sudo chmod 0700 "$EXPORT_DIR"
sudo chmod 0600 "$EXPORT_DIR"/*
```

Checksum values remain with the private backup set rather than being committed
to Git.

## Off-server copy

Set the connection and destination values privately:

```bash
OLD_ORIGIN_USER=remote_user
OLD_ORIGIN_IP=server_address
OLD_ORIGIN_KEY=/absolute/path/to/private-key.pem
REMOTE_EXPORT_DIR=/remote/export/path
LOCAL_EXPORT_DIR=/private/local/backup/path
```

Copy the export:

```bash
rsync \
  --archive \
  --human-readable \
  --info=progress2 \
  --rsync-path="sudo rsync" \
  --rsh="ssh -i $OLD_ORIGIN_KEY" \
  "${OLD_ORIGIN_USER}@${OLD_ORIGIN_IP}:${REMOTE_EXPORT_DIR}/" \
  "$LOCAL_EXPORT_DIR/"
```

Protect and verify the local copy:

```bash
chmod -R go-rwx "$LOCAL_EXPORT_DIR"

cd "$LOCAL_EXPORT_DIR"
sed -E 's#  .*/#  #' SHA256SUMS > SHA256SUMS.local
sha256sum --check SHA256SUMS.local
gzip --test wordpress.sql.gz
gzip --test wordpress-wp-content.tar.gz
```

The verified Phase 8 transfer passed all checksum and archive-integrity checks.

## Phase boundary

This phase created and verified the initial migration export. It did not import
data, change DNS, stop services or alter the live WordPress application.

The next phase transfers the verified export to the new server, imports the
database and content, adjusts ownership, and tests the migrated site before
cutover.