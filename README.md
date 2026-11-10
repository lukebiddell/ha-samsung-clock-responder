# Samsung Clock Responder: Home Assistant add-on

Keeps Samsung appliances' clocks set, and their energy reporting working,
while they're blocked from the internet.

Some Samsung appliances have no NTP client. They take the time from a
plain-HTTP connectivity check to `info.cspserver.net`. Without an answer,
their clock is never set and cumulative energy stops being reported. This
add-on answers that check locally.

[![Add repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Flukebiddell%2Fha-samsung-clock-responder)

## Add-ons

| Add-on | Description |
|---|---|
| [Samsung Clock Responder](samsung_clock_responder/) | Local stand-in for `info.cspserver.net/api/v1/connect-test` |

## Install

1. In Home Assistant, go to **Settings → Add-ons → Add-on Store → ⋮ →
   Repositories** and add `https://github.com/lukebiddell/ha-samsung-clock-responder`.
2. Install **Samsung Clock Responder** and start it.
3. Set up the DNS override and NAT rule on your router, as described in
   [the documentation](samsung_clock_responder/DOCS.md).

## How it was found

A Samsung washer, blocked from the internet and used through LocalThings,
kept reporting water use but no energy. Checking the washer's own data and
capturing its traffic showed:

- It never uses NTP.
- Its clock stays at a fixed 2025 date until a `GET` to
  `http://info.cspserver.net/api/v1/connect-test` succeeds.
- It won't connect if the name resolves to a private IP.
- Once a local server answered the check, through a public-IP DNS override
  plus destination NAT, the clock was correct within seconds. Energy
  reporting came back at the next hourly update.

## Development

```sh
python3 -m unittest discover -s tests
```

## License

[MIT](LICENSE)
