# Cleanprofs

This integration loads cleaning dates for your cleanprofs subscription based on postalcode and housenumber.

### Installation

Copy this folder to `<config_dir>/custom_components/cleanprofs/`.

Add the following entry in your `configuration.yaml`:

```yaml
sensor:
  - platform: cleanprofs
    postalcode: 1234AB
    housenumber: 12
```

You could use the following in automations:

```yaml
- alias: Clean container tomorrow
  trigger:
    - platform: time
      at: '20:00:00'
  condition:
    - condition: template
      value_template: "{{ states('sensor.cleanprofs_date_1') == (now() + timedelta(days=1)).strftime('%d-%m-%Y') }}"
  action:
    - service: notify.pushover
      data_template:
        title: "Container cleaning"
        message: "Tomorrow the container will be cleaned, leave outside until 19:00."
```
