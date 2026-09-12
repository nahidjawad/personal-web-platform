# Deployment Guide

## Purpose

This guide explains how to prepare a compatible Ubuntu server using the
Ansible automation in this repository.


## Prerequisites

The Ansible controller requires:

- A Linux environment such as Ubuntu under WSL 2
- Git
- OpenSSH
- `uv`
- Network access to the target server
- An SSH private key with access to the target server
- A supported target running Ubuntu 24.04 LTS

Production secrets and SSH private keys must remain outside this repository.

## Prepare the controller

Clone the repository:

```bash
git clone https://github.com/nahidjawad/personal-web-platform.git
cd personal-web-platform
```
Install the pinned Python and Ansible dependencies:
```bash
uv sync
```
Confirm the tools are available:
```bash
uv run python --version
uv run ansible --version
uv run ansible-lint --version
```

## Create the production inventory

Copy the safe inventory example:
```bash
cp ansible/inventories/example/hosts.yml \
  ansible/inventories/production/hosts.yml
```
Edit the production inventory and provide:

* The server's static public IP address
* The remote SSH user
* The absolute path to the SSH private key

The production inventory is intentionally ignored by Git.

Verify that Git ignores it:
```bash
git check-ignore -v ansible/inventories/production/hosts.yml
```
## Verify connectivity
Change to the Ansible directory:
```bash
cd ansible
```
Confirm that Ansible can reach the target:
```bash 
uv run ansible web_servers \
  --module-name ansible.builtin.ping
```
Expected result:
```bash
personal-web-prod-01 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```
Do not apply configuration until connectivity succeeds.

## Validate the automation

Run linting:
```bash
uv run ansible-lint
```
Run syntax checks for the playbooks:
```bash
for playbook in playbooks/*.yml; do
  uv run ansible-playbook "$playbook" --syntax-check
done
```
## Apply the host configuration

Run the preflight inspection:
```bash
uv run ansible-playbook playbooks/preflight.yml
```
Apply the operating-system baseline:
```bash
uv run ansible-playbook playbooks/baseline.yml
```
If the baseline reports that a reboot is required, run:
```bash
uv run ansible-playbook playbooks/reboot-if-required.yml
```
Configure persistent swap:
```bash
uv run ansible-playbook playbooks/swap.yml
```
Configure the host firewall:
```bash
uv run ansible-playbook playbooks/security.yml
```
Keep a second SSH session open while initially enabling or changing firewall
rules. Confirm that SSH still works before closing the original session.

Install and configure Docker:
```bash
uv run ansible-playbook playbooks/docker.yml
```

## Prepare the Compose platform directories

Create the application deployment directories:

```bash
uv run ansible-playbook playbooks/compose-platform.yml
```
This creates the deployment root, Nginx configuration directories and the
root-restricted secrets directory.

The playbook also deploys `compose.yaml`, generates the non-secret `.env` file
and validates the resulting Compose configuration.

Validate it manually when required:

```bash
cd /srv/personal-web-platform
sudo docker compose --env-file .env config --quiet
```
## Create application secrets

Run the interactive secrets playbook from the Ansible directory:

```bash
uv run ansible-playbook playbooks/application-secrets.yml
```
The playbook prompts without displaying the passwords and creates protected
files under `/srv/personal-web-platform/secrets`. Re-running it preserves
existing secret values.

## Start the application stack

Connect to the server and run:
```bash
cd /srv/personal-web-platform
sudo docker compose --env-file .env pull
sudo docker compose --env-file .env up --detach --wait
sudo docker compose --env-file .env ps
curl --fail http://127.0.0.1/platform-health
```
MariaDB should report `healthy`, all three services should be running, and the
health endpoint should return `ok`.

## Deploy Cloudflare Origin CA TLS

Create an Origin CA certificate in Cloudflare covering:

```text
chintavabna.com
*.chintavabna.com
```

Store the certificate and private key outside the repository.

Deploy them from the Ansible controller:

```bash
cd ansible
uv run ansible-playbook playbooks/origin-tls.yml
```

Provide the absolute local certificate and private-key paths when prompted.

Deploy the updated Compose and Nginx configuration:

```bash
uv run ansible-playbook playbooks/compose-platform.yml
```

Validate Nginx in a disposable container before recreating the proxy:

```bash
uv run ansible web_servers \
  --become \
  --module-name ansible.builtin.shell \
  --args "cd /srv/personal-web-platform && docker compose --env-file .env run --rm --no-deps proxy nginx -t"
```

Recreate WordPress with forwarded HTTPS awareness:

```bash
uv run ansible web_servers \
  --become \
  --module-name ansible.builtin.shell \
  --args "cd /srv/personal-web-platform && docker compose --env-file .env up --detach --no-deps --force-recreate --wait wordpress"
```

Recreate the proxy with its TLS mounts and published HTTPS port:

```bash
uv run ansible web_servers \
  --become \
  --module-name ansible.builtin.shell \
  --args "cd /srv/personal-web-platform && docker compose --env-file .env up --detach --no-deps --force-recreate --wait proxy"
```

Validate the running proxy:

```bash
uv run ansible web_servers \
  --become \
  --module-name ansible.builtin.shell \
  --args "cd /srv/personal-web-platform && docker compose --env-file .env exec proxy nginx -t"
```

Cloudflare Origin CA certificates are intended for Cloudflare-to-origin
connections. Direct browser testing may report an untrusted certificate even
when the origin is configured correctly.

## Verify idempotency

Run each configuration playbook a second time after its initial successful
application.

For example:
```bash
uv run ansible-playbook playbooks/docker.yml
```
The expected recap is:
```yaml
changed=0
unreachable=0
failed=0
```
A repeatable playbook should make no changes when the server already matches
the declared configuration.

## Verify Docker

Run a disposable test container:
```bash
uv run ansible web_servers \
  --become \
  --module-name ansible.builtin.command \
  --args "docker run --rm hello-world"
```
Inspect the Docker daemon:
```bash
uv run ansible web_servers \
  --become \
  --module-name ansible.builtin.command \
  --args "docker info"
```
Confirm that the test container was removed:
```bash
uv run ansible web_servers \
  --become \
  --module-name ansible.builtin.command \
  --args "docker ps --all"
```
## Administrative access

The normal SSH user is not added to the docker group because that group
provides effective root-level control of the host.

Use sudo docker during an interactive SSH session. Ansible uses privilege
escalation through become: true.

## WordPress update policy

WordPress core releases are applied by changing the pinned WordPress container
image, deploying it and validating the site. Automatic in-application core
updates are disabled.

Plugins and themes can still be managed through WordPress administration
because `wp-content` is stored in its own persistent named volume.

## Current limitation

Scheduled backups, retention, notifications and restoration testing remain
Phase 11 work. The Phase 9 pre-cutover backup is a manually created and
checksum-verified recovery checkpoint.