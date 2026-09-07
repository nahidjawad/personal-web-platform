# Operations Guide

## Scope

This guide contains tested operational procedures for the personal web
platform. It will expand as the application stack, backups and monitoring are
implemented.

The current version covers the Docker host only.

## Check Docker service state

Connect to the server and run:

```bash
sudo systemctl status docker
```
For a machine-readable result:
```bash
sudo systemctl is-active docker
sudo systemctl is-enabled docker
```
Expected results are active and enabled.

## Inspect Docker

Show Docker runtime information:
```bash
sudo docker info
```
Show running containers:
```bash
sudo docker ps
```
Show running and stopped containers:
```bash
sudo docker ps --all
```
Show downloaded images:
```bash
sudo docker image ls
```
Show Docker disk usage:
```bash
sudo docker system df
```
## Inspect Docker service logs

Show recent daemon logs:
```bash
sudo journalctl --unit docker --since today
```
Follow new Docker daemon messages:
```bash
sudo journalctl --unit docker --follow
```
Press Ctrl+C to stop following the log.

## Restart Docker

A manual Docker restart should be exceptional:
```bash
sudo systemctl restart docker
```
Before restarting Docker on a production server, check the running containers
and understand the potential application impact:
```bash
sudo docker ps
```
The Ansible-managed live-restore setting allows running containers to remain
active during some daemon interruptions, but it is not a replacement for
normal maintenance planning.

## Check host resources

Check memory and swap:
```bash
free -h
swapon --show
```
Check filesystem usage:
```bash
df -h
```
Check listening ports:
```bash
sudo ss --tcp --udp --listening --processes --numeric
```
## Docker Compose operations

Application-specific Compose commands will be added after the Compose stack is
implemented and verified.

That section will include:

* Starting and stopping the stack
* Checking container health
* Viewing application logs
* Pulling updated images
* Applying deployments
* Rolling back a failed deployment
* Safely restarting individual services

This intentionally avoids pretending that an application deployment already exists.