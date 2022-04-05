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
