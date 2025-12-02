"""Cloud Functions entry point for Marketing KPI Reporter.

This module provides the entry point for Google Cloud Functions to execute
the daily marketing KPI analysis and reporting workflow.

Environment Variables Required:
    GCP_PROJECT_ID: Google Cloud project ID
    GA4_DATASET: BigQuery dataset name for GA4 data
    GOOGLE_ADS_DATASET: BigQuery dataset name for Google Ads data
    SEARCH_CONSOLE_DATASET: BigQuery dataset name for Search Console data
    HUBSPOT_DATASET: BigQuery dataset name for HubSpot data
    AI_PROVIDER: AI provider to use ('openai' or 'vertexai')
    OPENAI_API_KEY: OpenAI API key (required if AI_PROVIDER is 'openai')
    SLACK_WEBHOOK_URL: Slack incoming webhook URL
    SLACK_BOT_TOKEN: Slack bot token (alternative to webhook)
    SLACK_CHANNEL: Slack channel to post reports to
    REPORT_LANGUAGE: Language for reports ('ja' or 'en', default: 'ja')
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

import functions_framework
from flask import Request

from ai_reporter import AIReporter
from bigquery_client import BigQueryClient
from kpi_analyzer import KPIAnalyzer
from slack_notifier import SlackNotifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_config() -> dict[str, Any]:
    """Get configuration from environment variables.

    Returns:
        Dictionary containing configuration values
    """
    return {
        "gcp_project_id": os.environ.get("GCP_PROJECT_ID"),
        "dataset_config": {
            "ga4_dataset": os.environ.get("GA4_DATASET", "analytics_XXXXXXXXX"),
            "google_ads_dataset": os.environ.get(
                "GOOGLE_ADS_DATASET", "google_ads_transfer"
            ),
            "search_console_dataset": os.environ.get(
                "SEARCH_CONSOLE_DATASET", "searchconsole_data"
            ),
            "hubspot_dataset": os.environ.get("HUBSPOT_DATASET", "hubspot_data"),
        },
        "ai_provider": os.environ.get("AI_PROVIDER", "openai"),
        "openai_api_key": os.environ.get("OPENAI_API_KEY"),
        "slack_webhook_url": os.environ.get("SLACK_WEBHOOK_URL"),
        "slack_bot_token": os.environ.get("SLACK_BOT_TOKEN"),
        "slack_channel": os.environ.get("SLACK_CHANNEL", "#marketing-reports"),
        "report_language": os.environ.get("REPORT_LANGUAGE", "ja"),
        "gcp_location": os.environ.get("GCP_LOCATION", "us-central1"),
    }


def validate_config(config: dict[str, Any]) -> list[str]:
    """Validate configuration and return list of errors.

    Args:
        config: Configuration dictionary

    Returns:
        List of validation error messages
    """
    errors = []

    if not config.get("gcp_project_id"):
        errors.append("GCP_PROJECT_ID is required")

    if not config.get("slack_webhook_url") and not config.get("slack_bot_token"):
        errors.append("Either SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN is required")

    ai_provider = config.get("ai_provider", "").lower()
    if ai_provider == "openai" and not config.get("openai_api_key"):
        errors.append("OPENAI_API_KEY is required when AI_PROVIDER is 'openai'")

    return errors


def run_kpi_analysis(config: dict[str, Any]) -> dict[str, Any]:
    """Run the KPI analysis workflow.

    Args:
        config: Configuration dictionary

    Returns:
        Dictionary containing analysis results and report
    """
    logger.info("Starting KPI analysis workflow")

    logger.info("Fetching metrics from BigQuery")
    bq_client = BigQueryClient(
        project_id=config["gcp_project_id"],
        dataset_config=config["dataset_config"],
    )
    metrics = bq_client.get_all_metrics()
    logger.info("Successfully fetched metrics from all data sources")

    logger.info("Analyzing KPIs")
    analyzer = KPIAnalyzer(metrics)
    analysis = analyzer.get_full_analysis()
    logger.info("KPI analysis completed")

    logger.info(f"Generating report using {config['ai_provider']}")
    ai_reporter = AIReporter(
        provider=config["ai_provider"],
        openai_api_key=config.get("openai_api_key"),
        gcp_project_id=config["gcp_project_id"],
        gcp_location=config.get("gcp_location", "us-central1"),
    )
    report_text = ai_reporter.generate_report(
        analysis, language=config.get("report_language", "ja")
    )
    logger.info("Report generated successfully")

    alert_message = ai_reporter.generate_alert_message(analysis)

    return {
        "metrics": metrics,
        "analysis": analysis,
        "report_text": report_text,
        "alert_message": alert_message,
    }


def send_to_slack(
    config: dict[str, Any], report_text: str, alert_message: str | None = None
) -> dict[str, Any]:
    """Send report and alerts to Slack.

    Args:
        config: Configuration dictionary
        report_text: Generated report text
        alert_message: Optional alert message

    Returns:
        Dictionary containing Slack API responses
    """
    logger.info("Sending report to Slack")

    notifier = SlackNotifier(
        webhook_url=config.get("slack_webhook_url"),
        bot_token=config.get("slack_bot_token"),
        default_channel=config.get("slack_channel"),
    )

    report_response = notifier.send_report(report_text)
    logger.info(f"Report sent to Slack: {report_response}")

    alert_response = None
    if alert_message:
        logger.info("Sending alert to Slack")
        alert_response = notifier.send_alert(alert_message)
        logger.info(f"Alert sent to Slack: {alert_response}")

    return {
        "report_response": report_response,
        "alert_response": alert_response,
    }


@functions_framework.http
def marketing_kpi_report(request: Request) -> tuple[str, int]:
    """HTTP Cloud Function entry point for marketing KPI report.

    Args:
        request: Flask request object

    Returns:
        Tuple of (response_body, status_code)
    """
    logger.info("Marketing KPI Report function triggered")

    try:
        config = get_config()

        validation_errors = validate_config(config)
        if validation_errors:
            error_msg = f"Configuration errors: {', '.join(validation_errors)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg}), 400

        results = run_kpi_analysis(config)

        slack_results = send_to_slack(
            config,
            results["report_text"],
            results.get("alert_message"),
        )

        response = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "analysis_date": results["analysis"]["analysis_date"],
            "slack_results": slack_results,
        }

        logger.info("Marketing KPI Report completed successfully")
        return json.dumps(response, default=str), 200

    except Exception as e:
        logger.exception(f"Error in marketing_kpi_report: {e}")
        return json.dumps({"error": str(e)}), 500


@functions_framework.cloud_event
def marketing_kpi_report_pubsub(cloud_event: Any) -> None:
    """Pub/Sub Cloud Function entry point for scheduled execution.

    This function is triggered by Cloud Scheduler via Pub/Sub.

    Args:
        cloud_event: CloudEvent object containing Pub/Sub message
    """
    logger.info("Marketing KPI Report triggered via Pub/Sub")

    try:
        config = get_config()

        validation_errors = validate_config(config)
        if validation_errors:
            error_msg = f"Configuration errors: {', '.join(validation_errors)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        results = run_kpi_analysis(config)

        send_to_slack(
            config,
            results["report_text"],
            results.get("alert_message"),
        )

        logger.info("Marketing KPI Report completed successfully")

    except Exception as e:
        logger.exception(f"Error in marketing_kpi_report_pubsub: {e}")
        raise


def main() -> None:
    """Main function for local testing."""
    print("Running Marketing KPI Reporter locally...")

    config = get_config()

    validation_errors = validate_config(config)
    if validation_errors:
        print(f"Configuration errors: {validation_errors}")
        print("\nPlease set the following environment variables:")
        print("  - GCP_PROJECT_ID")
        print("  - GA4_DATASET")
        print("  - GOOGLE_ADS_DATASET")
        print("  - SEARCH_CONSOLE_DATASET")
        print("  - HUBSPOT_DATASET")
        print("  - AI_PROVIDER (openai or vertexai)")
        print("  - OPENAI_API_KEY (if using OpenAI)")
        print("  - SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN")
        return

    try:
        results = run_kpi_analysis(config)
        print("\n=== Generated Report ===")
        print(results["report_text"])

        if results.get("alert_message"):
            print("\n=== Alerts ===")
            print(results["alert_message"])

        send_to_slack(
            config,
            results["report_text"],
            results.get("alert_message"),
        )
        print("\nReport sent to Slack successfully!")

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
