"""BigQuery client for fetching marketing KPI data."""

from datetime import datetime, timedelta
from typing import Any

from google.cloud import bigquery


class BigQueryClient:
    """Client for executing BigQuery queries with date partitioning."""

    def __init__(self, project_id: str, dataset_config: dict[str, str]):
        """Initialize BigQuery client.

        Args:
            project_id: GCP project ID
            dataset_config: Dictionary containing dataset names for each data source
                - ga4_dataset: GA4 dataset name
                - google_ads_dataset: Google Ads dataset name
                - search_console_dataset: Search Console dataset name
                - hubspot_dataset: HubSpot dataset name
        """
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        self.dataset_config = dataset_config

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
        ga4_dataset = self.dataset_config.get("ga4_dataset", "analytics_XXXXXXXXX")

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
                `{self.project_id}.{ga4_dataset}.events_*`
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
                `{self.project_id}.{ga4_dataset}.events_*`
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
        start_date, end_date = self._get_date_range()
        ads_dataset = self.dataset_config.get(
            "google_ads_dataset", "google_ads_transfer"
        )

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
            `{self.project_id}.{ads_dataset}.p_ads_CampaignStats_*`
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

    def get_search_console_metrics(self) -> dict[str, Any]:
        """Fetch Search Console metrics for the last 7 days.

        Returns:
            Dictionary containing Search Console KPIs
        """
        start_date, end_date = self._get_date_range()
        sc_dataset = self.dataset_config.get(
            "search_console_dataset", "searchconsole_data"
        )

        query = f"""
        SELECT
            data_date AS date,
            SUM(impressions) AS impressions,
            SUM(clicks) AS clicks,
            SAFE_DIVIDE(SUM(clicks), SUM(impressions)) * 100 AS ctr,
            AVG(position) AS avg_position
        FROM
            `{self.project_id}.{sc_dataset}.searchdata_site_impression`
        WHERE
            data_date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
        GROUP BY
            data_date
        ORDER BY
            data_date DESC
        """

        results = self._execute_query(query)

        top_queries_query = f"""
        SELECT
            query,
            SUM(impressions) AS impressions,
            SUM(clicks) AS clicks,
            SAFE_DIVIDE(SUM(clicks), SUM(impressions)) * 100 AS ctr,
            AVG(position) AS avg_position
        FROM
            `{self.project_id}.{sc_dataset}.searchdata_site_impression`
        WHERE
            data_date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
            AND query IS NOT NULL
        GROUP BY
            query
        ORDER BY
            clicks DESC
        LIMIT 10
        """

        top_queries = self._execute_query(top_queries_query)

        top_pages_query = f"""
        SELECT
            url,
            SUM(impressions) AS impressions,
            SUM(clicks) AS clicks,
            SAFE_DIVIDE(SUM(clicks), SUM(impressions)) * 100 AS ctr,
            AVG(position) AS avg_position
        FROM
            `{self.project_id}.{sc_dataset}.searchdata_url_impression`
        WHERE
            data_date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
        GROUP BY
            url
        ORDER BY
            clicks DESC
        LIMIT 10
        """

        top_pages = self._execute_query(top_pages_query)

        total_impressions = sum(r.get("impressions", 0) or 0 for r in results)
        total_clicks = sum(r.get("clicks", 0) or 0 for r in results)

        return {
            "source": "Search Console",
            "period": f"{start_date} to {end_date}",
            "daily_data": results,
            "top_queries": top_queries,
            "top_pages": top_pages,
            "summary": {
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "avg_ctr": (
                    round(total_clicks / total_impressions * 100, 2)
                    if total_impressions
                    else 0
                ),
                "avg_position": (
                    round(
                        sum(r.get("avg_position", 0) or 0 for r in results)
                        / len(results),
                        1,
                    )
                    if results
                    else 0
                ),
            },
        }

    def get_hubspot_metrics(self) -> dict[str, Any]:
        """Fetch HubSpot metrics for the last 7 days.

        Returns:
            Dictionary containing HubSpot KPIs
        """
        start_date, end_date = self._get_date_range()
        hubspot_dataset = self.dataset_config.get("hubspot_dataset", "hubspot_data")

        contacts_query = f"""
        SELECT
            DATE(createdate) AS date,
            COUNT(*) AS new_contacts,
            COUNTIF(lifecyclestage = 'lead') AS new_leads,
            COUNTIF(lifecyclestage = 'marketingqualifiedlead') AS new_mqls,
            COUNTIF(lifecyclestage = 'salesqualifiedlead') AS new_sqls
        FROM
            `{self.project_id}.{hubspot_dataset}.contacts`
        WHERE
            DATE(createdate) BETWEEN DATE('{start_date}') AND DATE('{end_date}')
        GROUP BY
            date
        ORDER BY
            date DESC
        """

        contacts_results = self._execute_query(contacts_query)

        deals_query = f"""
        SELECT
            DATE(createdate) AS date,
            COUNT(*) AS new_deals,
            SUM(amount) AS pipeline_value,
            COUNTIF(dealstage = 'closedwon') AS closed_won,
            SUM(CASE WHEN dealstage = 'closedwon' THEN amount ELSE 0 END) AS closed_won_value
        FROM
            `{self.project_id}.{hubspot_dataset}.deals`
        WHERE
            DATE(createdate) BETWEEN DATE('{start_date}') AND DATE('{end_date}')
        GROUP BY
            date
        ORDER BY
            date DESC
        """

        deals_results = self._execute_query(deals_query)

        email_query = f"""
        SELECT
            DATE(timestamp) AS date,
            COUNTIF(type = 'SENT') AS emails_sent,
            COUNTIF(type = 'OPEN') AS emails_opened,
            COUNTIF(type = 'CLICK') AS emails_clicked,
            SAFE_DIVIDE(COUNTIF(type = 'OPEN'), COUNTIF(type = 'SENT')) * 100 AS open_rate,
            SAFE_DIVIDE(COUNTIF(type = 'CLICK'), COUNTIF(type = 'OPEN')) * 100 AS click_rate
        FROM
            `{self.project_id}.{hubspot_dataset}.email_events`
        WHERE
            DATE(timestamp) BETWEEN DATE('{start_date}') AND DATE('{end_date}')
        GROUP BY
            date
        ORDER BY
            date DESC
        """

        email_results = self._execute_query(email_query)

        total_new_contacts = sum(r.get("new_contacts", 0) or 0 for r in contacts_results)
        total_new_leads = sum(r.get("new_leads", 0) or 0 for r in contacts_results)
        total_new_mqls = sum(r.get("new_mqls", 0) or 0 for r in contacts_results)
        total_new_deals = sum(r.get("new_deals", 0) or 0 for r in deals_results)
        total_pipeline_value = sum(
            r.get("pipeline_value", 0) or 0 for r in deals_results
        )
        total_closed_won = sum(r.get("closed_won", 0) or 0 for r in deals_results)
        total_closed_won_value = sum(
            r.get("closed_won_value", 0) or 0 for r in deals_results
        )
        total_emails_sent = sum(r.get("emails_sent", 0) or 0 for r in email_results)
        total_emails_opened = sum(r.get("emails_opened", 0) or 0 for r in email_results)

        return {
            "source": "HubSpot",
            "period": f"{start_date} to {end_date}",
            "contacts_data": contacts_results,
            "deals_data": deals_results,
            "email_data": email_results,
            "summary": {
                "total_new_contacts": total_new_contacts,
                "total_new_leads": total_new_leads,
                "total_new_mqls": total_new_mqls,
                "total_new_deals": total_new_deals,
                "total_pipeline_value": round(total_pipeline_value, 2),
                "total_closed_won": total_closed_won,
                "total_closed_won_value": round(total_closed_won_value, 2),
                "total_emails_sent": total_emails_sent,
                "avg_open_rate": (
                    round(total_emails_opened / total_emails_sent * 100, 2)
                    if total_emails_sent
                    else 0
                ),
            },
        }

    def get_all_metrics(self) -> dict[str, Any]:
        """Fetch all marketing metrics from all data sources.

        Returns:
            Dictionary containing all KPIs from all sources
        """
        return {
            "ga4": self.get_ga4_metrics(),
            "google_ads": self.get_google_ads_metrics(),
            "search_console": self.get_search_console_metrics(),
            "hubspot": self.get_hubspot_metrics(),
        }
