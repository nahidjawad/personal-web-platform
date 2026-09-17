#!/usr/bin/env python3
"""Review or apply the public IPv4 web firewall for the Lightsail origin.

Run from AWS CloudShell. The default action only prints the proposed rules.
"""

import argparse
import ipaddress
import json
import subprocess
import sys
from pathlib import Path

INSTANCE = "personal-web-prod-01"
REGION = "ap-south-1"
RANGES = Path(__file__).resolve().parents[1] / "config" / "cloudflare-ips-v4.txt"


def aws(*args):
    result = subprocess.run(
        ["aws", "lightsail", *args, "--region", REGION, "--output", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def ranges():
    values = [
        line.strip() for line in RANGES.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    networks = [ipaddress.ip_network(value, strict=True) for value in values]
    if not 10 <= len(networks) <= 30 or len(set(networks)) != len(networks):
        raise ValueError("Expected 10 to 30 distinct Cloudflare IPv4 CIDRs")
    if any(net.version != 4 or net.prefixlen == 0 for net in networks):
        raise ValueError("Only restricted IPv4 ranges are allowed")
    return [str(net) for net in networks]


def rule(port, cidrs):
    return {"fromPort": port, "toPort": port, "protocol": "tcp", "cidrs": cidrs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=["plan", "apply", "rollback"], nargs="?", default="plan"
    )
    args = parser.parse_args()
    cloudflare = ranges()
    states = aws("get-instance-port-states", "--instance-name", INSTANCE)["portStates"]
    by_port = {state["fromPort"]: state for state in states}
    if len(states) != 3 or set(by_port) != {22, 80, 443}:
        raise ValueError("Unexpected port set; preserve extra rules manually")
    for port in (22, 80, 443):
        state = by_port[port]
        if state["toPort"] != port or state["protocol"] != "tcp":
            raise ValueError(f"Unexpected protocol/port range on {port}")
        if state.get("ipv6Cidrs"):
            raise ValueError("Unexpected IPv6 rules; review IPv6 before changing")
    ssh = by_port[22]
    if ssh.get("cidrs") != ["0.0.0.0/0"]:
        raise ValueError("SSH no longer matches the recorded IPv4 rule")
    if set(ssh.get("cidrListAliases", [])) - {"lightsail-connect-ipv6"}:
        raise ValueError("Unexpected SSH alias; review before changing")
    for port in (80, 443):
        current = set(by_port[port].get("cidrs", []))
        if current != {"0.0.0.0/0"}:
            if not 10 <= len(current) <= 30 or any(
                ipaddress.ip_network(value, strict=True).version != 4
                or ipaddress.ip_network(value, strict=True).prefixlen == 0
                for value in current
            ):
                raise ValueError(f"Unexpected source ranges on {port}")
        if by_port[port].get("cidrListAliases"):
            raise ValueError(f"Unexpected alias on {port}")

    ssh_rule = rule(22, ["0.0.0.0/0"])
    # IPv6 is disabled for this instance. The reported IPv6 browser-SSH
    # alias is omitted; IPv4 browser SSH remains covered by 0.0.0.0/0.
    target = [ssh_rule, rule(80, cloudflare), rule(443, cloudflare)]
    rollback = [
        ssh_rule, rule(80, ["0.0.0.0/0"]), rule(443, ["0.0.0.0/0"])
    ]
    chosen = rollback if args.action == "rollback" else target
    print(json.dumps(chosen, indent=2))
    if args.action == "plan":
        print("Read-only plan. Check the source list against https://www.cloudflare.com/ips-v4", file=sys.stderr)
        return
    if all(
        set(by_port[port].get("cidrs", [])) == set(chosen[index]["cidrs"])
        for index, port in ((1, 80), (2, 443))
    ):
        print("Web rules already match the requested state.", file=sys.stderr)
        return
    operation = aws(
        "put-instance-public-ports", "--instance-name", INSTANCE,
        "--port-infos", json.dumps(chosen)
    )["operation"]
    print(f"AWS operation: {operation['status']}", file=sys.stderr)
    if operation["status"] in {"Failed"}:
        raise RuntimeError(operation.get("errorDetails", "AWS operation failed"))
    observed = aws("get-instance-port-states", "--instance-name", INSTANCE)["portStates"]
    actual = {state["fromPort"]: state for state in observed}
    if set(actual) != {22, 80, 443} or any(
        set(actual[port].get("cidrs", [])) != set(chosen[index]["cidrs"])
        for index, port in ((0, 22), (1, 80), (2, 443))
    ):
        raise RuntimeError("Rules have not reached the requested state; inspect AWS")
    print("Observed all three requested IPv4 rules.", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Firewall update stopped: {exc}", file=sys.stderr)
        sys.exit(1)
