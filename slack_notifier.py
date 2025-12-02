"""Slack Notifier for sending marketing reports to Slack channels."""

import os
from typing import Any

import requests


class SlackNotifier:
    """Notifier for sending messages to Slack channels."""

    def __init__(
        self,
        webhook_url: str | None = None,
        bot_token: str | None = None,
        default_channel: str | None = None,
    ):
        """Initialize Slack Notifier.

        Args:
            webhook_url: Slack incoming webhook URL
            bot_token: Slack bot token (for Bot API)
            default_channel: Default channel to post to (for Bot API)
        """
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
        self.bot_token = bot_token or os.environ.get("SLACK_BOT_TOKEN")
        self.default_channel = default_channel or os.environ.get(
            "SLACK_DEFAULT_CHANNEL", "#marketing-reports"
        )

        if not self.webhook_url and not self.bot_token:
            raise ValueError(
                "Either SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN must be provided"
            )

    def send_report(
        self,
        report_text: str,
        channel: str | None = None,
        thread_ts: str | None = None,
    ) -> dict[str, Any]:
        """Send a marketing report to Slack.

        Args:
            report_text: The report text to send
            channel: Channel to post to (overrides default)
            thread_ts: Thread timestamp to reply to

        Returns:
            Response from Slack API
        """
        if self.webhook_url:
            return self._send_via_webhook(report_text)
        else:
            return self._send_via_bot_api(report_text, channel, thread_ts)

    def _send_via_webhook(self, report_text: str) -> dict[str, Any]:
        """Send message via incoming webhook.

        Args:
            report_text: The report text to send

        Returns:
            Response status
        """
        payload = {
            "text": report_text,
            "mrkdwn": True,
        }

        response = requests.post(
            self.webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code == 200:
            return {"ok": True, "status_code": response.status_code}
        else:
            return {
                "ok": False,
                "status_code": response.status_code,
                "error": response.text,
            }

    def _send_via_bot_api(
        self,
        report_text: str,
        channel: str | None = None,
        thread_ts: str | None = None,
    ) -> dict[str, Any]:
        """Send message via Slack Bot API.

        Args:
            report_text: The report text to send
            channel: Channel to post to
            thread_ts: Thread timestamp to reply to

        Returns:
            Response from Slack API
        """
        target_channel = channel or self.default_channel

        payload = {
            "channel": target_channel,
            "text": report_text,
            "mrkdwn": True,
        }

        if thread_ts:
            payload["thread_ts"] = thread_ts

        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.bot_token}",
            },
            timeout=30,
        )

        return response.json()

    def send_alert(
        self,
        alert_text: str,
        channel: str | None = None,
        mention_users: list[str] | None = None,
    ) -> dict[str, Any]:
        """Send an alert message to Slack.

        Args:
            alert_text: The alert text to send
            channel: Channel to post to
            mention_users: List of user IDs to mention

        Returns:
            Response from Slack API
        """
        if mention_users:
            mentions = " ".join([f"<@{user_id}>" for user_id in mention_users])
            alert_text = f"{mentions}\n\n{alert_text}"

        return self.send_report(alert_text, channel)

    def send_formatted_report(
        self,
        report_data: dict[str, Any],
        channel: str | None = None,
    ) -> dict[str, Any]:
        """Send a formatted report with blocks to Slack.

        Args:
            report_data: Dictionary containing report sections
            channel: Channel to post to

        Returns:
            Response from Slack API
        """
        blocks = self._build_report_blocks(report_data)

        if self.webhook_url:
            payload = {
                "blocks": blocks,
                "text": "Daily Marketing KPI Report",
            }
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            if response.status_code == 200:
                return {"ok": True, "status_code": response.status_code}
            else:
                return {
                    "ok": False,
                    "status_code": response.status_code,
                    "error": response.text,
                }
        else:
            target_channel = channel or self.default_channel
            payload = {
                "channel": target_channel,
                "blocks": blocks,
                "text": "Daily Marketing KPI Report",
            }
            response = requests.post(
                "https://slack.com/api/chat.postMessage",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.bot_token}",
                },
                timeout=30,
            )
            return response.json()

    def _build_report_blocks(self, report_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Build Slack blocks for formatted report.

        Args:
            report_data: Dictionary containing report sections

        Returns:
            List of Slack block elements
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":chart_with_upwards_trend: Daily Marketing KPI Report",
                    "emoji": True,
                },
            },
            {"type": "divider"},
        ]

        executive_summary = report_data.get("executive_summary", {})
        if executive_summary:
            summary_text = (
                f"*Total Traffic:* {executive_summary.get('total_website_traffic', 0):,}\n"
                f"*Ad Spend:* ${executive_summary.get('total_ad_spend', 0):,.2f}\n"
                f"*Conversions:* {executive_summary.get('total_ad_conversions', 0):,}\n"
                f"*New Leads:* {executive_summary.get('total_new_leads', 0):,}\n"
                f"*Revenue:* ${executive_summary.get('total_revenue', 0):,.2f}"
            )
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Executive Summary*\n{summary_text}"},
                }
            )
            blocks.append({"type": "divider"})

        for source in ["ga4", "google_ads", "search_console", "hubspot"]:
            source_data = report_data.get(source, {})
            if source_data:
                source_name = source_data.get("source", source.upper())
                summary = source_data.get("summary", {})
                insights = source_data.get("insights", [])

                summary_items = [f"*{k}:* {v}" for k, v in list(summary.items())[:5]]
                summary_text = "\n".join(summary_items)

                blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{source_name}*\n{summary_text}",
                        },
                    }
                )

                if insights:
                    insights_text = "\n".join([f"• {insight}" for insight in insights[:3]])
                    blocks.append(
                        {
                            "type": "context",
                            "elements": [{"type": "mrkdwn", "text": insights_text}],
                        }
                    )

        blocks.append({"type": "divider"})
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Report generated on {report_data.get('analysis_date', 'N/A')}",
                    }
                ],
            }
        )

        return blocks
