# Samsung Clock Responder

## Why this exists

Some Samsung appliances have no NTP client. They set their clock from the
reply to one plain-HTTP request:

```
GET http://info.cspserver.net/api/v1/connect-test
```

If you block the appliance from the internet (for example to keep it local
with [LocalThings](https://github.com/mbillow/localthings)), that request
never gets an answer and the clock is never set. After a power cut it falls
back to a fixed date in the past. The appliance keeps working, but it stops
reporting cumulative energy, so energy sensors in Home Assistant freeze.

This add-on answers the request from your own network, with the same reply
Samsung's server sends. The request contains no device identifiers, and the
appliance stays blocked from the internet.

Confirmed on a Samsung WW90CGC04DAEEU washer (`DA_WM_TP1_21_COMMON` board).
Other appliances on the same board are likely to behave the same way. Other
models are untested.

## Network setup

The add-on alone isn't enough: the appliance has to be sent to it. You need a
router that can do both of these:

1. **DNS override.** Make `info.cspserver.net` resolve to a **public** IP.
   Use one of Samsung's own addresses, such as `13.196.92.18`. The appliance
   looks the name up but won't connect if the answer is a private (LAN)
   address, so pointing the name straight at Home Assistant doesn't work.
2. **Destination NAT.** Redirect TCP traffic from the appliance to that IP on
   port 80 to your Home Assistant host, on the port this add-on uses
   (80 by default).

UniFi, OPNsense, pfSense, OpenWrt and MikroTik routers can do this. Most ISP
routers can't.

The appliance and Home Assistant must be on **different subnets** (for
example an IoT VLAN), so replies pass back through the router. On the same
subnet, the reply comes straight from Home Assistant's address, and the
appliance ignores it. That case needs extra hairpin NAT and hasn't been
tested.

### UniFi (tested)

In **Settings → Policy Engine → Policy Table → Create New Policy**:

| Policy | Settings |
|---|---|
| DNS Host (A) | `info.cspserver.net` → `13.196.92.18` |
| NAT → Dest. NAT | Interface: the appliance's network. Protocol TCP. Source: the appliance's IP. Destination: `13.196.92.18`, port `80`. Translated IP: your Home Assistant IP. |

You can leave an existing "block internet" firewall rule as it is.

### OpenWrt (untested example)

```
# /etc/config/dhcp, under config dnsmasq
list address '/info.cspserver.net/13.196.92.18'

# /etc/config/firewall
config redirect
	option name 'samsung-clock'
	option target 'DNAT'
	option src 'iot'
	option src_ip '192.168.50.22'
	option src_dip '13.196.92.18'
	option src_dport '80'
	option proto 'tcp'
	option dest 'lan'
	option dest_ip '192.168.1.86'
	option dest_port '80'
```

### OPNsense / pfSense (untested outline)

Add an Unbound **Host Override** for `info.cspserver.net` → `13.196.92.18`.
Then add a **NAT Port Forward** on the appliance's interface: TCP, source
the appliance, destination `13.196.92.18` port 80, redirect target your Home
Assistant IP and port.

## Configuration

| Option | Default | Description |
|---|---|---|
| `log_requests` | `true` | Log one line per request. |

The listening port can be changed under the add-on's **Network** settings.
If you change it, use the same port as the NAT rule's target.

## Checking it works

1. Start the add-on and open its **Log** tab.
2. Turn the appliance off at the wall and back on. The check happens while
   the appliance thinks it's offline, usually within a minute of booting.
3. A line like this should appear:

   ```
   2026-11-10T23:05:53+00:00 192.168.50.22 'GET /api/v1/connect-test HTTP/1.1' Host='info.cspserver.net'
   ```

4. Cumulative energy comes back at the appliance's next hourly update.

## Things to know

- **A one-off catch-up when you first set it up.** The appliance keeps
  counting while its clock is wrong, but doesn't report. When the clock is
  first set, everything used since the clock was lost arrives in one hourly
  update, so energy statistics and cost trackers show it all in that hour.
  Adjust them in **Developer tools → Statistics** if needed. After that, as
  long as the add-on is running, the clock is set within a minute of each
  power-up and no backlog builds up. A jump only happens again if the
  appliance runs while the add-on or the NAT rule is down.
- **Hourly granularity.** The appliance updates cumulative energy on the
  hour, in 0.1 kWh steps. On a time-of-use tariff, cost lands in the slot
  after the energy was used.
- **Keep the add-on running.** The appliance's clock resets on power loss.
  The add-on starts on boot and has a health check; turn on **Watchdog** on
  the add-on's Info tab so Home Assistant restarts it if it stops responding.
- **What gets answered.** Every request gets the same empty `200` reply,
  whatever its path.
