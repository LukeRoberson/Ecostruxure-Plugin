"""
Module: event_handler.py

Handle webhook events from EcoStruxure and process them accordingly.

Classes:
    EventHandler: Class to handle webhook events from EcoStruxure.
        It validates the webhook, extracts common and specific fields,
        and processes the event to send logs to the logging service.

Dependencies:
    requests: For making HTTP requests to the logging service and
        fetching plugin configuration.
    logging: For logging errors and debug messages.
    yaml: For loading event handling configuration from a YAML file.
    flask: For accessing the current application context.
"""

# Standard library imports
import logging
import yaml
import requests
from flask import current_app
from datetime import datetime


PLUGINS_URL = "http://core:5100/api/plugins"
BASIC_AUTH_URL = "http://security:5100/api/basic"


# Get event handling configuration from the YAML file
with open("events.yaml", "r") as file:
    EVENTS = yaml.safe_load(file)


class EventHandler:
    """
    EventHandler class to handle webhook events from EcoStruxure.

    Args:
        config (dict): Configuration dictionary containing necessary settings.
    """

    def __init__(
        self,
        config
    ) -> None:
        """
        Initialize the EventHandler with the provided configuration.

        Args:
            config (dict):
                Configuration dictionary containing necessary settings.

        Returns:
            None
        """

        self.config = config
        self.plugin_name = config['name']
        self.default_chat = config.get('chats', {}).get('default', None)

    def __enter__(
        self
    ) -> 'EventHandler':
        """
        Enter the runtime context related to this object.

        Args:
            None

        Returns:
            EventHandler: The current instance of EventHandler.
        """

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ) -> None:
        """
        Exit the runtime context related to this object.

        Args:
            exc_type: The exception type.
            exc_value: The exception value.
            traceback: The traceback object.

        Returns:
            None
        """

        # Handle any cleanup if necessary
        if exc_type is not None:
            # Log the exception or handle it as needed
            print(f"Exception occurred: {exc_value}")

    def _validate_webhook(
        self,
    ) -> bool:
        """
        Validate the authenticity of the webhook request.

        Args:
            None

        Returns:
            bool: True if the webhook is valid, False otherwise.
        """

        try:
            response = requests.post(
                BASIC_AUTH_URL,
                json={
                    "plugin": self.plugin_name,
                    "auth": self.basic_auth,
                },
            )

            if response.status_code != 200:
                logging.error(
                    "Failed to validate webhook: %s",
                    response.text
                )
                return False

        except Exception as e:
            logging.error("Error validating webhook: %s", e)
            return False

        return True

    def _extract_fields(
        self,
        event: dict,
    ) -> None:
        """
        Extract common fields from the event data.

        Args:
            event (dict): The event data.

        Returns:
            None
        """

        # Save the event data
        self.event = event
        self.alert_type = None

        # Event activation details
        self.activ_activated_at = event.get("activation_details", {}).get(
            "activated_at", ""
        )
        self.activ_label = event.get("activation_details", {}).get(
            "label", ""
        ).replace(" ", "_")
        self.activ_message = event.get("activation_details", {}).get(
            "message", ""
        )

        # Event updated details
        if event.get("updated_details", None) is not None:
            self.updated_label = event.get("updated_details", {}).get(
                "label", ""
            )
            self.updated_message = event.get("updated_details", {}).get(
                "message", ""
            )
            self.updated_severity = event.get("updated_details", {}).get(
                "current_severity", "info"
            )
        else:
            self.updated_label = None
            self.updated_message = None
            self.updated_severity = None

        # Event cleared details
        if event.get("cleared_details", None) is not None:
            self.cleared_at = event.get("cleared_details", {}).get(
                "cleared_at", ""
            )

            start = datetime.fromisoformat(
                self.activ_activated_at.replace("Z", "+00:00")
            )
            end = datetime.fromisoformat(
                self.cleared_at.replace("Z", "+00:00")
            )
            self.duration = (end - start).total_seconds()

        else:
            self.cleared_at = None

        # Work out the event status
        if self.cleared_at:
            self.status = "cleared"
        elif self.updated_label:
            self.status = "updated"
        else:
            self.status = "activated"

        # Get the timestamp of the event
        if self.status == "activated" or self.status == "updated":
            self.ts = self.activ_activated_at
        elif self.status == "cleared":
            self.ts = self.cleared_at

        # Get the severity of the event
        if self.updated_severity:
            self.severity = self.updated_severity
        else:
            self.severity = event.get("current_severity_peak", "info")

        # Get main fields from the event
        self.id = event.get("id", "")
        self.org_id = event.get("organization_details", {}).get("id", "")
        self.org_name = event.get("organization_details", {}).get("name", "")

        # Get device details
        self.device_id = event.get("device_details", {}).get(
            "id", ""
        )
        self.device_label = event.get("device_details", {}).get(
            "label", ""
        )
        self.device_model = event.get("device_details", {}).get(
            "model", ""
        )
        self.device_type = event.get("device_details", {}).get(
            "device_type", ""
        )
        self.device_ipv4 = event.get("device_details", {}).get(
            "ipv4_addresses", ""
        )
        self.device_ipv6 = event.get("device_details", {}).get(
            "ipv6_addresses", ""
        )
        self.device_mac = event.get("device_details", {}).get(
            "mac_addresses", ""
        )

        # Get location details
        self.location_ancestors = event.get("location_details", {}).get(
            "location_ancestors", []
        )

        # Get the alert type
        if self.status == "activated" and self.activ_label:
            self.alert_type = f"{self.activ_label.replace(' ', '_')}_Activated"
        elif self.status == "updated" and self.updated_label:
            self.alert_type = f"{self.updated_label.replace(' ', '_')}_Updated"
        elif self.status == "cleared" and self.updated_label:
            self.alert_type = f"{self.updated_label.replace(' ', '_')}_Cleared"
        else:
            self.alert_type = "Unknown Event"

    def _parse_event(
        self,
    ) -> dict:
        """
        Parse the event data to extract relevant information.

        Args:
            None

        Returns:
            dict: A dictionary containing the parsed event data.
        """

        message = ""

        # Get the handler for the alert type
        if self.alert_type == "Unknown Event":
            logging.error(
                f"Unknown alert type for event: {self.event}. "
                "Cannot process event."
            )
            message = f"Unknown EcoStruxure event:\n{self.event}"
            self.teams_msg = f"Unknown EcoStruxure event: {self.event}"
            self.severity = "warning"
            self.alert_type = "Unknown Event"
            self.status = "unknown"

        else:
            handler = EVENTS.get(self.alert_type, None)
            if handler is None:
                logging.error(
                    f"Unhandled alert type: {self.alert_type}. "
                    "Cannot process event."
                )
                message = f"Unhandled EcoStruxure event: {self.event}:\n"
                if self.status:
                    message += f"Status: {self.status}\n"
                if self.alert_type:
                    message += f"Alert Type: {self.alert_type}\n"

            else:
                try:
                    # Get the formatted message
                    message = handler.get(
                        "message",
                        self.event
                    ).format(self=self)

                    # If there is a Teams message (optional), get it too
                    self.teams_msg = handler.get("teams", None)
                    if self.teams_msg:
                        self.teams_msg = self.teams_msg.format(self=self)

                except Exception as e:
                    logging.error(
                        f"Error formatting event message for {self.event}:"
                        f"\n{e}"
                    )
                    message = "No message included"
                    self.teams_msg = str(self.event)
                    self.severity = "warning"

        log = {
            "source": "EcoStruxure",
            "log": {
                "group": "EcoStruxure",
                "category": self.status,
                "alert": self.alert_type,
                "severity": self.severity,
                "timestamp": self.ts,
                "message": message,
            },
            "teams": {
                "destination": self.config['chats']['default'],
                "message": message,
            }
        }

        return log

    def process_event(
        self,
        event: dict,
        headers: dict,
    ) -> None:
        """
        Basic processing of a webhook event from Cloudflare.
            Extracts fields from the event and stores them in the instance.

        Args:
            event (dict): The event data received from Cloudflare.

        Returns:
            None
        """

        # Validate the webhook request
        self.basic_auth = headers.get("Authorization", "")
        result = self._validate_webhook()
        if not result:
            logging.error("Webhook validation failed.")
            return

        # Process each event in the webhook
        for entry in event:
            self._extract_fields(entry)
            log = self._parse_event()

            # Get the actions to perform
            if self.alert_type in self.config:
                actions = self.config[self.alert_type]
            else:
                actions = self.config["default"]

            # Convert this to a list of actions
            action_list = []
            action_list = [
                k for k in ("web", "teams", "syslog", "sql") if actions.get(k)
            ]
            log["destination"] = action_list

            # If no actions are specified, do nothing
            if not action_list:
                return

            # Check if there is a custom chat ID for Teams messages
            chat_ids = (
                current_app.config.get('PLUGIN_CONFIG', {}).get('chats', {})
            )
            teams_chat = chat_ids.get('default', None)
            if 'chat' in actions:
                teams_chat = chat_ids.get(
                    actions['chat'], None
                )

            # Log to logging service
            system_log = current_app.config['SYSTEM_LOG']
            system_log.log(
                message=log['log']['message'],
                destination=log['destination'],
                group=log['log']['group'],
                category=log['log']['category'],
                alert=log['log']['alert'],
                severity=log['log']['severity'],
                teams_msg=log['teams']['message'],
                chat_id=teams_chat,
            )
