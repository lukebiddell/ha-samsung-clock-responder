# Samsung Clock Responder

Answers Samsung appliances' plain-HTTP connectivity check
(`info.cspserver.net/api/v1/connect-test`) on your own network. An appliance
blocked from the internet then still sets its clock, and keeps reporting
energy to integrations like LocalThings.

Needs a DNS override and a destination-NAT rule on your router. See the
**Documentation** tab.
