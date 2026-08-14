# A separate Wi-Fi segment for IoT, and how to reach it

[Русская версия](../ru/002-iot-network-segment.md)

## Why a separate network at all

Cheap Wi-Fi gadgets and a modern home network don't mix well, for 2 reasons.

**The technical one.** IoT devices support a narrow set of parameters. Almost all of them are 2.4 GHz
only, many need a 20 MHz channel, and they trip over modern access point options. Your main network,
on the other hand, is where you want current standards: 5 GHz, wide channels, seamless roaming between
access points, up-to-date encryption. Those are exactly the settings that make a ten-dollar smart plug
drop off or refuse to join.

Splitting them means you stop choosing between "works for everything" and "decent speed and security".
The IoT network can be tuned strictly to what those devices need:

- 2.4 GHz only;
- 20 MHz channel;
- no mesh, no seamless roaming;
- extra options disabled, the ones a cheap Wi-Fi module chokes on.

**The security one.** You don't control the firmware, updates arrive from a vendor cloud, and there are
no sources. Keeping such a device on the same network as your work laptop, NAS and Home Assistant is
risk for no benefit. Security is never wasted effort — let the trinkets live apart.

In the examples below: `192.168.10.0/24` is the main network, `192.168.30.0/24` is IoT.

## The problem segmentation brings with it

Local control of a Tuya device needs a TCP connection to port 6668. Home Assistant lives in the main
network, the device in the IoT one. Several unpleasant things follow.

### Auto-discovery doesn't cross segments

Tuya devices announce themselves with broadcasts to `255.255.255.255`. A router does **not** forward
those between segments — that's a property of broadcast itself, and no firewall rule changes it.

So: you'll have to set the device address by hand, and `tinytuya scan` from another subnet won't find
it. Only `scan -force 192.168.30.0/24` helps, because it probes addresses directly.

Which leads to the next point: **pin the device IP** by MAC in your router's DHCP. The integration
talks to an address; if DHCP hands out a different one, everything breaks.

### Client isolation on the access point

The nastiest item, because it looks like a dead device. Symptom: the device is online in the cloud, the
app controls it fine, but from a laptop on the same network it answers neither ping nor ARP:

```
$ arp -n 192.168.30.16
? (192.168.30.16) at (incomplete) on en0
```

`(incomplete)` means the device didn't even answer an ARP request. The check is simple — sweep the
subnet and see who replies:

```bash
for i in $(seq 1 254); do ping -c1 -W 150 192.168.30.$i >/dev/null 2>&1 & done; wait
arp -an | grep 192.168.30
```

The commands in this recipe are macOS. On Linux use `ip neigh` instead of `arp` and `ip route get`
instead of `route -n get`, and note that `ping -W` counts seconds there, not milliseconds.

If only the gateway and yourself show up, **client isolation** is on. It stops devices in one segment
from seeing each other, and it's enabled by default on guest networks. Turn it off in the access point
settings.

### A firewall rule — not a route, not port forwarding

When segments don't talk, the first instinct is "I need a route" or "I need port forwarding". Both are
wrong.

**Port forwarding** is for inbound connections from the internet. Both of your addresses are local,
nothing leaves the house.

**A route** on the router isn't needed either: both subnets are its own interfaces, it knows them by
definition, and clients know the gateway. Packets do reach the router and get **dropped by the
filter** — they aren't lost for lack of a route.

What you need is a permit rule in the firewall. The key detail: the rule goes on the interface the
traffic **enters the router from**, that is the main segment where Home Assistant sits. Return packets
are handled by connection tracking, no separate rule required.

The minimal version, only what control needs:

| Parameter | Value |
|---|---|
| Interface | main segment (`192.168.10.0/24`) |
| Action | Permit |
| Source | Any |
| Destination | `192.168.30.16` |
| Protocol | TCP |
| Destination port | 6668 |

With that rule control works but ping doesn't — ICMP isn't covered. That's a consequence, not a bug.
If you want ping for diagnostics, add a second rule for ICMP. A second one, specifically: some firmware
(Keenetic, for one) won't let a rule match "any protocol", only a specific one.

Opening the whole subnet is fine too, as long as you keep the direction in mind. Permitting **main →
IoT** is low risk: your house reaches the gadgets, they still can't reach your house. The dangerous
direction is the opposite one, and that's the one you leave closed. This asymmetry is the entire point
of splitting the networks.

Opening UDP for the sake of auto-discovery is pointless, by the way — broadcast won't cross segments
regardless.

## Laptop, VPN and a static route

A separate story is the machine you debug all this from.

If your laptop runs a full-tunnel VPN, it replaces the default route. It looks like this:

```
$ netstat -rn -f inet | grep -E "^(default|0/1|128\.0/1)"
0/1                utun5              UScg                utun5
default            utun5              UScg                utun5
128.0/1            utun5              USc                 utun5
```

The `0.0.0.0/1` and `128.0.0.0/1` pair covers everything except directly connected subnets. So your
packets never reach the IoT segment — they go into the tunnel. To see where traffic to the device
goes:

```bash
route -n get 192.168.30.16 | grep -E "interface|gateway"
```

If `interface` shows `utunN`, the VPN is the culprit.

You don't have to turn the VPN off. Route selection uses the longest matching prefix, so a more
specific route wins over `/1`:

```bash
sudo route -n add -net 192.168.30.0/24 192.168.10.1
```

Where `192.168.10.1` is your main network gateway. After that, traffic to the IoT segment goes locally
and everything else keeps using the tunnel.

Caveats:

- the route won't survive a reboot, and often not a VPN reconnect either — the client rewrites the
  table;
- for a permanent fix, look for a "don't tunnel local networks" option in the VPN client;
- Home Assistant isn't affected: it has no VPN, and the router rule is enough for it.

One more thing for later: don't identify a tunnel by interface number. `utunN` numbers shift between
reboots, and the same VPN was `utun5` yesterday and `utun1` today. Look at the interface address instead
(`ifconfig utunN`): Tailscale uses the `100.64.0.0/10` range, WireGuard clients usually something in
`10.x`. Mine had grabbed the default route with a `10.8.x.x` address — and it wasn't Tailscale, which I
blamed and spent half an hour disabling.

## Diagnostic order

When local control doesn't work, check in this order — cheapest first:

1. `route -n get <ip>` — where do packets go at all. If into a tunnel, stop here.
2. `ping <ip>` — does the device answer. No answer while it's online in the cloud means client
   isolation or an inter-segment filter, almost always.
3. `arp -n <ip>` — `(incomplete)` confirms the device doesn't hear us at link level.
4. `nc -vz <ip> 6668` — check the port directly. Open means the network is fine and the problem is a
   layer up.
5. Only then look at keys, protocols and versions.
