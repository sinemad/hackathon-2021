# hackathon-2021

ArubaOS-CX Network Analytics Engine (NAE) scripts, built for the Aruba 2021 hackathon


[Network Analytics Engine (NAE)](https://www.arubanetworks.com/products/switches/network-analytics-engine/)
is an ArubaOS-CX feature that runs Python monitoring agents directly on the switch.
An agent subscribes to REST-exposed switch state (interface counters, link state,
VSX health, etc.) and reacts to defined conditions in real time — logging events,
raising alerts, or issuing CLI commands — with no external polling server required.
See the [ArubaOS-CX NAE Scripting Guide](https://techhub.hpe.com/eginfolib/Aruba/OS-CX_10.04/5200-6724/index.html)
for the full agent/script API reference, and Aruba's
[nae-scripts repository](https://github.com/aruba/nae-scripts) for more example agents.

## Scripts

### `port_dot1x_user_label.py` (current)

Monitors interface link state. When a port comes up, the agent queries
`port_access_clients` for that port; if the client authenticated via 802.1X, the
agent rewrites the interface description to `authenticated user - <username>`. When
the port goes down, the description is cleared. Every action is also written to the
NAE debug log and syslog, and the agent raises a Minor alert while a labeled port is
active.

Example debug output for user `rpi` connecting on `1/1/1`:

```
|LOG_DEBUG|================ Up ================
|LOG_DEBUG|Interface 1/1/1 is up
|LOG_DEBUG|HTTP GET status: 200
|LOG_DEBUG|USERNAME: rpi
|LOG_DEBUG|User rpi logged in on port 1/1/1
|LOG_DEBUG|COMMAND EXECUTED: config interface 1/1/1 description logged in user - rpi exit exit
|LOG_DEBUG|COMMAND EXECUTED: show interface 1/1/1
|LOG_DEBUG|================ /Up ================
```

**Caveats**
- Only labels ports authenticated via 802.1X (no MAC Authentication support yet).
- NAE agents currently target the v1 REST API, so the trigger is limited to
  interface up/down transitions rather than the authentication event itself.

**TODO**
- Add MAC Authentication support (label the port with the client's MAC address).

### `interface_link_state_monitor.py` (reference)

The upstream [Aruba NAE example script](https://github.com/aruba/nae-scripts) that
`port_dot1x_user_label.py` was derived from. It only tracks link up/down transitions
and syslogs/alerts on them — no REST lookups or description changes. Kept here as a
reference for the monitor/rule structure reused above.

## Requirements

- An ArubaOS-CX switch running firmware **10.04** or later with NAE enabled.
- Switch management access to upload/install NAE agent scripts (CLI or REST API).

## Installing an agent

1. Copy the script content into the switch via the NAE script editor, or upload it
   with the REST API / CLI (`nae-script` commands), per the
   [ArubaOS-CX NAE documentation](https://techhub.hpe.com/eginfolib/Aruba/OS-CX_10.04/5200-6724/index.html).
2. Create an agent instance from the script's `Manifest['Name']`.
3. Enable the agent on the interfaces/ports you want monitored.
4. Tail the agent's debug log (or syslog) to confirm rules are firing as expected.

## License

Apache License 2.0 — see the license header in each script.
