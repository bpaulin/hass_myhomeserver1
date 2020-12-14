# hass_myhomeserver1

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
![](https://github.com/bpaulin/brownpaperbag/workflows/build/badge.svg)

hass_myhomeserver1 is a custom component for home assistant to manage lights and covers with myhomeserver gateway.


## Prerequisites

Before you begin, ensure you have met the following requirements:

 * You have a [myhomeserver1 gateway] on your network
 * You have set the open password on your gateway
 * You have installed the latest version of [home assistant]
 * You have installed [HACS] on your home assistant

## Installing hass_myhomeserver1

 * add this repository to HACS custom repositories
 * install **myhomeserver1** integration

## Configuration

somewhere in your home assistant configuration, set:

```yaml
myhomeserver1:
  host: <GATEWAY IP>
  port: <GATEWAY PORT>
  password: <OPEN PASSWORD>

light:
  # ...
  - platform: myhomeserver1

cover:
  # ...
  - platform: myhomeserver1
```

[myhomeserver1 gateway]: https://www.legrand.co.uk/products/user-interface/home-automation/myhome/myhomeserver1
[home assistant]: https://www.home-assistant.io/
[HACS]: https://hacs.xyz/

