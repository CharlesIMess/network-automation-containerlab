# netlab - container-based network lab + Python automation

## Prerequisites (Linux, or WSL2 on Windows)
1. Docker
2. Containerlab: `bash -c "$(curl -sL https://get.containerlab.dev)"`
3. Python deps: `python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`

## Run
    sudo containerlab deploy -t topology.clab.yml   # start the 3 routers
    python deploy.py render                         # preview config
    python deploy.py deploy                         # push + commit
    python deploy.py verify                         # ping all peers
    sudo containerlab destroy -t topology.clab.yml  # tear down

Inspect a router manually: `ssh admin@clab-netlab-leaf1` (password `NokiaSrl1!`)
or `docker exec -it clab-netlab-leaf1 sr_cli`.

## Moving to real hardware
Change hostnames/credentials in `inventory/`, add a template named after the
Netmiko platform (e.g. `cisco_ios.j2`, `arista_eos.j2`), and set `platform`
in groups.yaml. The workflow stays the same.
