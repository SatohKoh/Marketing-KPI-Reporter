"""BigQuery client for fetching GA4 and Google Ads KPI data."""

from datetime import datetime, timedelta
from typing import Any

from google.cloud import bigquery


class BigQueryClient:
    """Client for executing BigQuery queries with date partitioning."""

    def __init__(
        self,
        project_id: str,
        ga4_dataset: str,
        google_ads_dataset: str | None = None,
    ):
        """Initialize BigQuery client.

        Args:
            project_id: GCP project ID
            ga4_dataset: GA4 dataset name (e.g., analytics_123456789)
            google_ads_dataset: Google Ads dataset name (e.g., google_ads_data_transfer)
        """
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        self.ga4_dataset = ga4_dataset
        self.google_ads_dataset = google_ads_dataset

    def _get_date_range(self, days: int = 7) -> tuple[str, str]:
        """Get date range for partitioned queries.

        Args:
            days: Number of days to look back

        Returns:
            Tuple of (start_date, end_date) in YYYY-MM-DD format
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    def _execute_query(self, query: str) -> list[dict[str, Any]]:
        """Execute a BigQuery query and return results as list of dicts.

        Args:
            query: SQL query string

        Returns:
            List of dictionaries containing query results
        """
        query_job = self.client.query(query)
        results = query_job.result()
        return [dict(row) for row in results]

    def get_ga4_metrics(self) -> dict[str, Any]:
        """Fetch GA4 metrics for the last 7 days.

        Returns:
            Dictionary containing GA4 KPIs
        """
        start_date, end_date = self._get_date_range()

        query = f"""
        WITH daily_metrics AS (
            SELECT
                PARSE_DATE('%Y%m%d', event_date) AS date,
                COUNT(DISTINCT user_pseudo_id) AS users,
                COUNT(DISTINCT CASE WHEN (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') IS NOT NULL THEN CONCAT(user_pseudo_id, (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')) END) AS sessions,
                COUNTIF(event_name = 'page_view') AS pageviews,
                COUNTIF(event_name = 'first_visit') AS new_users,
                COUNTIF(event_name = 'purchase') AS purchases,
                SUM(CASE WHEN event_name = 'purchase' THEN (SELECT value.double_value FROM UNNEST(event_params) WHERE key = 'value') ELSE 0 END) AS revenue
            FROM
                `{self.project_id}.{self.ga4_dataset}.events_*`
            WHERE
                _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', DATE('{start_date}'))
                AND FORMAT_DATE('%Y%m%d', DATE('{end_date}'))
            GROUP BY
                date
        ),
        session_engagement AS (
            SELECT
                PARSE_DATE('%Y%m%d', event_date) AS date,
                COUNT(DISTINCT CONCAT(user_pseudo_id, (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id'))) AS total_sessions,
                COUNT(DISTINCT CASE
                    WHEN (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'session_engaged') = '1'
                    THEN CONCAT(user_pseudo_id, (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id'))
                END) AS engaged_sessions
            FROM
                `{self.project_id}.{self.ga4_dataset}.events_*`
            WHERE
                _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', DATE('{start_date}'))
                AND FORMAT_DATE('%Y%m%d', DATE('{end_date}'))
            GROUP BY
                date
        )
        SELECT
            dm.date,
            dm.users,
            dm.sessions,
            dm.pageviews,
            dm.new_users,
            dm.purchases,
            dm.revenue,
            SAFE_DIVIDE(se.total_sessions - se.engaged_sessions, se.total_sessions) * 100 AS bounce_rate
        FROM
            daily_metrics dm
        LEFT JOIN
            session_engagement se ON dm.date = se.date
        ORDER BY
            dm.date DESC
        """

        results = self._execute_query(query)

        total_users = sum(r.get("users", 0) or 0 for r in results)
        total_sessions = sum(r.get("sessions", 0) or 0 for r in results)
        total_pageviews = sum(r.get("pageviews", 0) or 0 for r in results)
        total_new_users = sum(r.get("new_users", 0) or 0 for r in results)
        total_purchases = sum(r.get("purchases", 0) or 0 for r in results)
        total_revenue = sum(r.get("revenue", 0) or 0 for r in results)
        avg_bounce_rate = (
            sum(r.get("bounce_rate", 0) or 0 for r in results) / len(results)
            if results
            else 0
        )

        return {
            "source": "GA4",
            "period": f"{start_date} to {end_date}",
            "daily_data": results,
            "summary": {
                "total_users": total_users,
                "total_sessions": total_sessions,
                "total_pageviews": total_pageviews,
                "total_new_users": total_new_users,
                "total_purchases": total_purchases,
                "total_revenue": total_revenue,
                "avg_bounce_rate": round(avg_bounce_rate, 2),
                "pages_per_session": (
                    round(total_pageviews / total_sessions, 2) if total_sessions else 0
                ),
            },
        }

    def get_google_ads_metrics(self) -> dict[str, Any]:
        """Fetch Google Ads metrics for the last 7 days.

        Returns:
            Dictionary containing Google Ads KPIs
        """
        if not self.google_ads_dataset:
            return {
                "source": "Google Ads",
                "period": "",
                "daily_data": [],
                "summary": {},
                "error": "Google Ads dataset not configured",
            }

        start_date, end_date = self._get_date_range()

        query = f"""
        SELECT
            segments_date AS date,
            SUM(metrics_impressions) AS impressions,
            SUM(metrics_clicks) AS clicks,
            SAFE_DIVIDE(SUM(metrics_clicks), SUM(metrics_impressions)) * 100 AS ctr,
            SUM(metrics_cost_micros) / 1000000 AS cost,
            SAFE_DIVIDE(SUM(metrics_cost_micros) / 1000000, SUM(metrics_clicks)) AS cpc,
            SUM(metrics_conversions) AS conversions,
            SAFE_DIVIDE(SUM(metrics_conversions), SUM(metrics_clicks)) * 100 AS conversion_rate,
            SAFE_DIVIDE(SUM(metrics_conversions_value), SUM(metrics_cost_micros) / 1000000) AS roas
        FROM
            `{self.project_id}.{self.google_ads_dataset}.p_ads_CampaignStats_*`
        WHERE
            _PARTITIONDATE BETWEEN DATE('{start_date}') AND DATE('{end_date}')
        GROUP BY
            segments_date
        ORDER BY
            segments_date DESC
        """

        results = self._execute_query(query)

        total_impressions = sum(r.get("impressions", 0) or 0 for r in results)
        total_clicks = sum(r.get("clicks", 0) or 0 for r in results)
        total_cost = sum(r.get("cost", 0) or 0 for r in results)
        total_conversions = sum(r.get("conversions", 0) or 0 for r in results)

        return {
            "source": "Google Ads",
            "period": f"{start_date} to {end_date}",
            "daily_data": results,
            "summary": {
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "avg_ctr": (
                    round(total_clicks / total_impressions * 100, 2)
                    if total_impressions
                    else 0
                ),
                "total_cost": round(total_cost, 2),
                "avg_cpc": round(total_cost / total_clicks, 2) if total_clicks else 0,
                "total_conversions": total_conversions,
                "conversion_rate": (
                    round(total_conversions / total_clicks * 100, 2)
                    if total_clicks
                    else 0
                ),
                "roas": (
                    round(
                        sum(r.get("roas", 0) or 0 for r in results) / len(results), 2
                    )
                    if results
                    else 0
                ),
            },
        }
