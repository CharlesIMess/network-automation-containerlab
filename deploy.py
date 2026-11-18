#!/usr/bin/env python3
"""Render, deploy, and verify device config with Nornir + Netmiko.

  python deploy.py render   # show generated config, touch nothing
  python deploy.py deploy   # push and commit config
  python deploy.py verify   # ping every point-to-point peer
"""
import argparse
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from nornir import InitNornir
from nornir.core.task import Result, Task
from nornir_netmiko.tasks import netmiko_send_command, netmiko_send_config
from nornir_utils.plugins.functions import print_result

BASE = Path(__file__).parent
JINJA = Environment(
    loader=FileSystemLoader(BASE / "templates"),
    undefined=StrictUndefined,  # fail loudly on missing data
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_config(task: Task) -> str:
    host_vars = {key: task.host[key] for key in task.host.keys()}  # incl. group data
    template = JINJA.get_template(f"{task.host.platform}.j2")
    return template.render(hostname=task.host.name, **host_vars)


def render(task: Task) -> Result:
    return Result(host=task.host, result=render_config(task))


def deploy(task: Task) -> Result:
    lines = [l for l in render_config(task).splitlines() if l.strip()]
    # Netmiko enters SR Linux candidate mode; "commit now" commits and exits it.
    task.run(
        netmiko_send_config,
        config_commands=lines + ["commit now"],
        exit_config_mode=False,
    )
    return Result(host=task.host, result=f"committed {len(lines)} lines", changed=True)


def verify(task: Task) -> Result:
    report, failed = [], False
    for intf in task.host["interfaces"]:
        out = task.run(
            netmiko_send_command,
            command_string=f"ping {intf['peer']} network-instance default -c 3",
            read_timeout=30,
        ).result
        ok = re.search(r"\b0% packet loss", out) is not None
        failed |= not ok
        report.append(f"{intf['name']} -> {intf['peer']}: {'OK' if ok else 'FAIL'}")
    return Result(host=task.host, result="\n".join(report), failed=failed)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["render", "deploy", "verify"])
    parser.add_argument("--hosts", nargs="*", help="limit to these hosts")
    args = parser.parse_args()

    nr = InitNornir(config_file=str(BASE / "config.yaml"))
    if args.hosts:
        nr = nr.filter(filter_func=lambda h: h.name in args.hosts)

    task = {"render": render, "deploy": deploy, "verify": verify}[args.action]
    print_result(nr.run(task=task))


if __name__ == "__main__":
    main()
