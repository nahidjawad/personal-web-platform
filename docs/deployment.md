# Deployment Guide

## Purpose

This guide explains how to prepare a compatible Ubuntu server using the
Ansible automation in this repository.

Application deployment instructions will be added when the Docker Compose
application stack is implemented and verified.

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
uv run ansible-playbook playbooks/reboot.yml
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

## Current limitation

This procedure currently prepares the server only. The Compose application
deployment, secrets, TLS, WordPress, MariaDB and migration procedures will be
added in later phases.