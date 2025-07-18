# Schneider Electric EcoStruxure Plugins


# Parsed Fields

The following fields are captured duting parsing, and can be used in event handling. Some come from the webhook directly, some are calculated based on webhook information.
</br></br>


In the _events.yaml_ file, access these using _self._ as the prefix. For example, _{self.event}_.

| Field              | Description                                         |
| ------------------ | --------------------------------------------------- |
| event              | The raw event from Ecostruxure                      |
| activ_activated_at | Event activation timestamp                          |
| activ_label        | Activation label (spaces replaced with underscores) |
| activ_message      | Activation message                                  |
| updated_label      | Updated label                                       |
| updated_message    | Updated message                                     |
| updated severity   | Updated severity                                    |
| cleared_at         | Event cleared timestamp                             |
| duration           | Calculated duration of the event                    |
| status             | Calculated: cleared, updated, or activated          |
| ts                 | Calculated event timestamp                          |
| severity           | Calculated severity                                 |
| id                 | Event ID                                            |
| org_id             | Organization ID                                     |
| org_name           | Organization name                                   |
| device_id          | The ID of the device                                |
| device_label       | The device's label (device name)                    |
| device_model       | The model of the device                             |
| device_type        | The type of the device                              |
| device_ipv4        | A list of IPv4 addresses for the device             |
| device_ipv6        | A list of IPv6 addresses for the device             |
| mac_address        | The MAC address of the device                       |
| location_ancestors | Location information                                |
</br></br>


Note: the _updated_, _cleared_, and _duration_ fields may not be present, depending on the alert.
</br></br>


# Webhooks

## Verification

Security can be set to one of:
* Basic Authentication: A username and password
* Token Authentication: A Bearer token is issued


## Headers

Standard headers are:

```json
{
    "Host": "ecostruxure:5000",
    "User-Agent": "Java-http-client/21.0.7",
    "Accept-Encoding": "gzip, br",
    "Accept": "*/*",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Cf-Ray": "95082d051ad4d46a-IAD",
    "X-Forwarded-For": "52.177.150.110",
    "Cf-Ipcountry": "US",
    "X-Forwarded-Proto": "https",
    "Authorization": "Basic a2FyZW46UGFzc3dvcmQwMA==",
    "Cf-Visitor": "{\"scheme\":\"https\"}",
    "Cf-Connecting-Ip": "52.177.150.110",
    "Cdn-Loop": "cloudflare; loops=1",
    "Content-Length": "861"
}
```
</br></br>

The **Authorization** header is particularly important for verifying the sender.


## Body

The body of the webhook will be a list, containing one or more events.

A new event will look like this:

```json
{
    "id": "00000000-0000-0000-0000-000000000000",
    "current_severity_peak": "WARNING",
    "organization_details": {
        "id": "00000000-0000-0000-0000-000000000000",
        "name": "ORGANIZATION NAME"
    },
    "device_details": {
        "id": "00000000-0000-0000-0000-000000000000",
        "label": "ASSET LABEL",
        "model": "ASSET MODEL",
        "device_type": "ASSET TYPE",
        "ip4_addresses": [
            "192.168.0.0",
            "192.168.1.1"
        ],
        "ip6_addresses": [
            "FE80:0000:0000:0000:abcd:abcd:abcd:abcd",
            "FE80:1111:1111:1111:abcd:abcd:abcd:abcd"
        ],
        "mac_addresses": [
            "00:00:00:00:00:00"
        ]
    },
    "location_details": {
        "location_ancestors": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "label": "LOCATION NAME 1"
            },
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "label": "LOCATION NAME 2"
            }
        ]
    },
    "activation_details": {
        "activated_at": "2025-06-16T06:15:58.409505938Z",
        "label": "ALARM ACTIVATION LABEL",
        "message": "ALARM MESSAGE"
    },
    "updated_details": null,
    "cleared_details": null
}
```
</br></br>


An update to an event will look like this:

```json
{
    "id": "00000000-0000-0000-0000-000000000000",
    "current_severity_peak": "CRITICAL",
    "organization_details": {
        "id": "00000000-0000-0000-0000-000000000000",
        "name": "ORGANIZATION NAME"
    },
    "device_details": {
        "id": "00000000-0000-0000-0000-000000000000",
        "label": "ASSET LABEL",
        "model": "ASSET MODEL",
        "device_type": "ASSET TYPE",
        "ip4_addresses": [
            "192.168.0.0",
            "192.168.1.1"
        ],
        "ip6_addresses": [
            "FE80:0000:0000:0000:abcd:abcd:abcd:abcd",
            "FE80:1111:1111:1111:abcd:abcd:abcd:abcd"
        ],
        "mac_addresses": [
            "00:00:00:00:00:00"
        ]
    },
    "location_details": {
        "location_ancestors": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "label": "LOCATION NAME 1"
            },
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "label": "LOCATION NAME 2"
            }
        ]
    },
    "activation_details": {
        "activated_at": "2025-06-16T06:15:58.409505938Z",
        "label": "ALARM ACTIVATION LABEL",
        "message": "ALARM MESSAGE"
    },
    "updated_details": {
        "label": "ALARM UPDATE LABEL",
        "message": "ALARM UPDATE MESSAGE",
        "current_severity": "CRITICAL"
    },
    "cleared_details": null
}
```


When an event is cleared (resolved), it will look like this:

```json
{
    "id": "00000000-0000-0000-0000-000000000000",
    "current_severity_peak": "CRITICAL",
    "organization_details": {
        "id": "00000000-0000-0000-0000-000000000000",
        "name": "ORGANIZATION NAME"
    },
    "device_details": {
        "id": "00000000-0000-0000-0000-000000000000",
        "label": "ASSET LABEL",
        "model": "ASSET MODEL",
        "device_type": "ASSET TYPE",
        "ip4_addresses": [
            "192.168.0.0",
            "192.168.1.1"
        ],
        "ip6_addresses": [
            "FE80:0000:0000:0000:abcd:abcd:abcd:abcd",
            "FE80:1111:1111:1111:abcd:abcd:abcd:abcd"
        ],
        "mac_addresses": [
            "00:00:00:00:00:00"
        ]
    },
    "location_details": {
        "location_ancestors": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "label": "LOCATION NAME 1"
            },
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "label": "LOCATION NAME 2"
            }
        ]
    },
    "activation_details": {
        "activated_at": "2025-06-16T06:15:58.409505938Z",
        "label": "ALARM ACTIVATION LABEL",
        "message": "ALARM MESSAGE"
    },
    "updated_details": {
        "label": "ALARM UPDATE LABEL",
        "message": "ALARM UPDATE MESSAGE",
        "current_severity": "CRITICAL"
    },
    "cleared_details": null
}
```

