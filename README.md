# Home Assistant configuration Kevin

Most of my configuration and some custom components.

Component overview
------------------
  * [Cure Waste component](#cure-waste-component)
  * [Feedparser component](#feedparser-component)
  * [Postcodeloterij component](#postcodeloterij-component)

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

sensor:
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

### Screenshot

<img src="https://raw.githubusercontent.com/kvanhoorn/hass/master/screenshots/cure_waste_dashboard.png" alt="Screenshot Cure Waste component" width="300">

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

## Feedparser component

This component calls RSS feeds to retrieve the latest item

### Installation

- Copy file 'custom_components/sensor/feedparser.py' to your '[ha_config_dir]/custom_components/sensor' directory;
- Configure with configuration below.
- Restart Home-Assistant

### Usage

To use this component in you installation, add the following to your 'configuration.yaml' file:

```yaml
# Example configuration.yaml entry

sensor:
  - platform: feedparser
    name: NOS Algemeen
    url: http://feeds.nos.nl/nosnieuwsalgemeen
    attributes:
      - link
```

Configuration variables:

- **name** (*Required*): Specify the name of these sensors, this can be your city or home name
- **url** (*Required*): Specify your postalcode, existing out of four numbers and two letters
- **title_attribute** (*Optional*): Specify the attribute that should be used as the value of the sensor (default 'title')
- **attributes** (*Optional*): Specify a list of extra attributes to append to the sensor (default: none)

### Screenshot

<img src="https://raw.githubusercontent.com/kvanhoorn/hass/master/screenshots/feedparser_dashboard.png" alt="Screenshot Feedparser component" width="300">

## Postcodeloterij component

This component checks your lottery winnings

### Installation

- Copy the files in 'custom_components/postcodeloterij/' to your '[ha_config_dir]/custom_components/postcodeloterij/' directory (create this folder first);
- Restart Home-Assistant so the component is loaded.
- Configure with configuration below.
- Restart Home-Assistant again

### Usage

To use this component in you installation, add the following to your 'configuration.yaml' file:

```yaml
# Example configuration.yaml entry

sensor:
  - platform: postcodeloterij
    postcode: 1234AB
```

Configuration variables:

- **postcode** (*Required*): Specify your postcode to retrieve winnings from

### Screenshot

<img src="https://raw.githubusercontent.com/kvanhoorn/hass/master/screenshots/postcodeloterij_dashboard.png" alt="Screenshot Postcodeloterij component" width="300">

#### Automation example

This automation will send the prizes as soon as the sensor updates:

```yaml
# can be pasted into automation.yaml, if you do that, remove the first line with automation:

automation:
- id: 1acc5110-8b4b-44b8-a5b5-43a445c41a0d
  alias: "00 - Prize Postcodeloterij"
  trigger:
    - platform: state
      entity_id: sensor.postcodeloterij_prijs
      not_to:
        - "0"
        - unavailable
        - unknown
  action:
    - alias: "Send notification"
      service: notify.mobile_app_<your_phone_here>
      data:
        title: "🏆 Winnen doe je bij..."
        message: >
          {% set p = trigger.to_state.state | int %}
          {% set m = 'prijs' if p == 1 else p ~ ' prijzen' %}
          {% set prizes = trigger.to_state.attriubutes.prizes %}
          "We hebben {{ m }}: {{ prizes }}"
        data:
          channel: LotteryPrize
          ttl: 0
          priority: high
          notification_icon: mdi:trophy
          tag: LotteryPrize
```
