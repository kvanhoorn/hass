# Home Assistant configuration Kevin

Most of my configuration and some custom components.

Component overview
------------------
  * [Cure Waste component](#cure-waste-component)

## Cure Waste component

This component queries the api of the Cure Waste app. It's only meant for the following Dutch municipalities:
* Eindhoven
* Geldrop-Mierlo
* Valkenswaard

### Installation

- Copy file 'custom_components/sensor/cure_waste.py' to your '[ha_config_dir]/custom_components/sensor' directory;
- Configure with configuration below.
- Restart Home-Assistant

### Usage

To use this component in you installation, add the following to your 'configuration.yaml' file:

```yaml
# Example configuration.yaml entry

sensors:
  - platform: cure_waste
    location: Eindhoven
    postalcode: 1234AB
    housenumber: 99
```

Configuration variables:

- **location** (*Required*): Specify the name of these sensors, this can be your city or home name
- **postalcode** (*Required*): Specify your postalcode, existing out of four numbers and two letters
- **housenumber** (*Required*): Specify your house number, excluding any suffix (not tested yet)

If you want to overwrite sensor names, head over to customization.yaml.
Sensors will be called: 'Eindhoven General waste'.

```yaml
# Example customize.yaml

# overwrite waste sensors
sensor.eindhoven_biodegradable_waste:
  friendly_name: GFT afval
sensor.eindhoven_biodegradable_waste_countdown:
  friendly_name: Dagen voor GFT

```

### Automation example

If you would like to receive a proper notification one day before, you could use an automation like in the xample below:

```yaml
# Example automation.yaml

- alias: Waste notification - paper
  trigger:
    platform: time
    at: '20:00:00'
  condition:
    condition: numeric_state
    entity_id: sensor.eindhoven_paper_waste_countdown
    below: 2
    above: 0
  action:
    - service: notify.pushover
      data:
        title: "Waste"
        message: "Tomorrow: Paper waste"

```
