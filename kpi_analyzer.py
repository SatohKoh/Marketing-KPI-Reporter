"""KPI Analyzer for aggregating and analyzing marketing metrics."""

from datetime import datetime
from typing import Any


class KPIAnalyzer:
    """Analyzer for marketing KPIs across multiple data sources."""

    def __init__(self, metrics_data: dict[str, Any]):
        """Initialize KPI Analyzer.

        Args:
            metrics_data: Dictionary containing metrics from all data sources
        """
        self.metrics = metrics_data
        self.analysis_date = datetime.now().strftime("%Y-%m-%d")

    def analyze_ga4(self) -> dict[str, Any]:
        """Analyze GA4 metrics and identify trends.

        Returns:
            Dictionary containing GA4 analysis
        """
        ga4_data = self.metrics.get("ga4", {})
        summary = ga4_data.get("summary", {})
        daily_data = ga4_data.get("daily_data", [])

        if len(daily_data) >= 2:
            latest = daily_data[0] if daily_data else {}
            previous = daily_data[1] if len(daily_data) > 1 else {}

            users_change = self._calculate_change(
                latest.get("users", 0), previous.get("users", 0)
            )
            sessions_change = self._calculate_change(
                latest.get("sessions", 0), previous.get("sessions", 0)
            )
            pageviews_change = self._calculate_change(
                latest.get("pageviews", 0), previous.get("pageviews", 0)
            )
        else:
            users_change = sessions_change = pageviews_change = 0

        return {
            "source": "GA4",
            "summary": summary,
            "trends": {
                "users_change_pct": users_change,
                "sessions_change_pct": sessions_change,
                "pageviews_change_pct": pageviews_change,
            },
            "insights": self._generate_ga4_insights(summary),
        }

    def analyze_google_ads(self) -> dict[str, Any]:
        """Analyze Google Ads metrics and identify trends.

        Returns:
            Dictionary containing Google Ads analysis
        """
        ads_data = self.metrics.get("google_ads", {})
        summary = ads_data.get("summary", {})
        daily_data = ads_data.get("daily_data", [])

        if len(daily_data) >= 2:
            latest = daily_data[0] if daily_data else {}
            previous = daily_data[1] if len(daily_data) > 1 else {}

            clicks_change = self._calculate_change(
                latest.get("clicks", 0), previous.get("clicks", 0)
            )
            cost_change = self._calculate_change(
                latest.get("cost", 0), previous.get("cost", 0)
            )
            conversions_change = self._calculate_change(
                latest.get("conversions", 0), previous.get("conversions", 0)
            )
        else:
            clicks_change = cost_change = conversions_change = 0

        return {
            "source": "Google Ads",
            "summary": summary,
            "trends": {
                "clicks_change_pct": clicks_change,
                "cost_change_pct": cost_change,
                "conversions_change_pct": conversions_change,
            },
            "insights": self._generate_ads_insights(summary),
        }

    def analyze_search_console(self) -> dict[str, Any]:
        """Analyze Search Console metrics and identify trends.

        Returns:
            Dictionary containing Search Console analysis
        """
        sc_data = self.metrics.get("search_console", {})
        summary = sc_data.get("summary", {})
        daily_data = sc_data.get("daily_data", [])
        top_queries = sc_data.get("top_queries", [])
        top_pages = sc_data.get("top_pages", [])

        if len(daily_data) >= 2:
            latest = daily_data[0] if daily_data else {}
            previous = daily_data[1] if len(daily_data) > 1 else {}

            impressions_change = self._calculate_change(
                latest.get("impressions", 0), previous.get("impressions", 0)
            )
            clicks_change = self._calculate_change(
                latest.get("clicks", 0), previous.get("clicks", 0)
            )
            position_change = self._calculate_change(
                previous.get("avg_position", 0), latest.get("avg_position", 0)
            )
        else:
            impressions_change = clicks_change = position_change = 0

        return {
            "source": "Search Console",
            "summary": summary,
            "top_queries": top_queries[:5],
            "top_pages": top_pages[:5],
            "trends": {
                "impressions_change_pct": impressions_change,
                "clicks_change_pct": clicks_change,
                "position_improvement_pct": position_change,
            },
            "insights": self._generate_seo_insights(summary, top_queries),
        }

    def analyze_hubspot(self) -> dict[str, Any]:
        """Analyze HubSpot metrics and identify trends.

        Returns:
            Dictionary containing HubSpot analysis
        """
        hubspot_data = self.metrics.get("hubspot", {})
        summary = hubspot_data.get("summary", {})
        contacts_data = hubspot_data.get("contacts_data", [])
        deals_data = hubspot_data.get("deals_data", [])

        if len(contacts_data) >= 2:
            latest = contacts_data[0] if contacts_data else {}
            previous = contacts_data[1] if len(contacts_data) > 1 else {}

            contacts_change = self._calculate_change(
                latest.get("new_contacts", 0), previous.get("new_contacts", 0)
            )
            leads_change = self._calculate_change(
                latest.get("new_leads", 0), previous.get("new_leads", 0)
            )
        else:
            contacts_change = leads_change = 0

        if len(deals_data) >= 2:
            latest_deals = deals_data[0] if deals_data else {}
            previous_deals = deals_data[1] if len(deals_data) > 1 else {}

            deals_change = self._calculate_change(
                latest_deals.get("new_deals", 0), previous_deals.get("new_deals", 0)
            )
        else:
            deals_change = 0

        return {
            "source": "HubSpot",
            "summary": summary,
            "trends": {
                "contacts_change_pct": contacts_change,
                "leads_change_pct": leads_change,
                "deals_change_pct": deals_change,
            },
            "insights": self._generate_hubspot_insights(summary),
        }

    def get_full_analysis(self) -> dict[str, Any]:
        """Get complete analysis of all marketing KPIs.

        Returns:
            Dictionary containing full analysis from all sources
        """
        return {
            "analysis_date": self.analysis_date,
            "ga4": self.analyze_ga4(),
            "google_ads": self.analyze_google_ads(),
            "search_console": self.analyze_search_console(),
            "hubspot": self.analyze_hubspot(),
            "executive_summary": self._generate_executive_summary(),
        }

    def _calculate_change(self, current: float, previous: float) -> float:
        """Calculate percentage change between two values.

        Args:
            current: Current value
            previous: Previous value

        Returns:
            Percentage change
        """
        if not previous:
            return 0
        return round(((current - previous) / previous) * 100, 2)

    def _generate_ga4_insights(self, summary: dict[str, Any]) -> list[str]:
        """Generate insights from GA4 data.

        Args:
            summary: GA4 summary data

        Returns:
            List of insight strings
        """
        insights = []

        bounce_rate = summary.get("avg_bounce_rate", 0)
        if bounce_rate > 70:
            insights.append(
                f"High bounce rate ({bounce_rate}%) - consider improving landing page experience"
            )
        elif bounce_rate < 40:
            insights.append(
                f"Excellent bounce rate ({bounce_rate}%) - users are engaged with content"
            )

        pages_per_session = summary.get("pages_per_session", 0)
        if pages_per_session < 2:
            insights.append(
                f"Low pages per session ({pages_per_session}) - improve internal linking"
            )
        elif pages_per_session > 4:
            insights.append(
                f"Strong engagement with {pages_per_session} pages per session"
            )

        new_user_ratio = (
            summary.get("total_new_users", 0) / summary.get("total_users", 1) * 100
        )
        if new_user_ratio > 70:
            insights.append(
                f"High new user ratio ({new_user_ratio:.1f}%) - good acquisition but focus on retention"
            )

        return insights

    def _generate_ads_insights(self, summary: dict[str, Any]) -> list[str]:
        """Generate insights from Google Ads data.

        Args:
            summary: Google Ads summary data

        Returns:
            List of insight strings
        """
        insights = []

        ctr = summary.get("avg_ctr", 0)
        if ctr < 2:
            insights.append(
                f"Low CTR ({ctr}%) - consider improving ad copy or targeting"
            )
        elif ctr > 5:
            insights.append(f"Excellent CTR ({ctr}%) - ads are resonating with audience")

        roas = summary.get("roas", 0)
        if roas < 1:
            insights.append(
                f"ROAS below 1 ({roas}) - ad spend exceeding revenue generated"
            )
        elif roas > 4:
            insights.append(f"Strong ROAS of {roas} - consider scaling successful campaigns")

        conversion_rate = summary.get("conversion_rate", 0)
        if conversion_rate < 2:
            insights.append(
                f"Low conversion rate ({conversion_rate}%) - optimize landing pages"
            )

        return insights

    def _generate_seo_insights(
        self, summary: dict[str, Any], top_queries: list[dict]
    ) -> list[str]:
        """Generate insights from Search Console data.

        Args:
            summary: Search Console summary data
            top_queries: Top performing queries

        Returns:
            List of insight strings
        """
        insights = []

        avg_position = summary.get("avg_position", 0)
        if avg_position > 20:
            insights.append(
                f"Average position ({avg_position}) needs improvement - focus on content optimization"
            )
        elif avg_position < 10:
            insights.append(
                f"Good average position ({avg_position}) - maintain SEO efforts"
            )

        ctr = summary.get("avg_ctr", 0)
        if ctr < 2 and avg_position < 10:
            insights.append(
                "Low CTR despite good rankings - improve meta titles and descriptions"
            )

        if top_queries:
            top_query = top_queries[0].get("query", "")
            if top_query:
                insights.append(f"Top performing query: '{top_query}'")

        return insights

    def _generate_hubspot_insights(self, summary: dict[str, Any]) -> list[str]:
        """Generate insights from HubSpot data.

        Args:
            summary: HubSpot summary data

        Returns:
            List of insight strings
        """
        insights = []

        new_contacts = summary.get("total_new_contacts", 0)
        new_leads = summary.get("total_new_leads", 0)

        if new_contacts > 0:
            lead_conversion = (new_leads / new_contacts) * 100
            if lead_conversion < 20:
                insights.append(
                    f"Low contact-to-lead conversion ({lead_conversion:.1f}%) - improve lead nurturing"
                )
            elif lead_conversion > 50:
                insights.append(
                    f"Strong lead conversion rate ({lead_conversion:.1f}%)"
                )

        open_rate = summary.get("avg_open_rate", 0)
        if open_rate < 20:
            insights.append(
                f"Low email open rate ({open_rate}%) - improve subject lines"
            )
        elif open_rate > 30:
            insights.append(f"Excellent email open rate ({open_rate}%)")

        closed_won = summary.get("total_closed_won", 0)
        closed_won_value = summary.get("total_closed_won_value", 0)
        if closed_won > 0:
            insights.append(
                f"Closed {closed_won} deals worth ${closed_won_value:,.2f}"
            )

        return insights

    def _generate_executive_summary(self) -> dict[str, Any]:
        """Generate executive summary of all marketing performance.

        Returns:
            Dictionary containing executive summary
        """
        ga4_summary = self.metrics.get("ga4", {}).get("summary", {})
        ads_summary = self.metrics.get("google_ads", {}).get("summary", {})
        sc_summary = self.metrics.get("search_console", {}).get("summary", {})
        hubspot_summary = self.metrics.get("hubspot", {}).get("summary", {})

        total_website_traffic = ga4_summary.get("total_sessions", 0)
        total_ad_spend = ads_summary.get("total_cost", 0)
        total_ad_conversions = ads_summary.get("total_conversions", 0)
        total_organic_clicks = sc_summary.get("total_clicks", 0)
        total_new_leads = hubspot_summary.get("total_new_leads", 0)
        total_revenue = ga4_summary.get("total_revenue", 0)

        cost_per_lead = (
            total_ad_spend / total_new_leads if total_new_leads > 0 else 0
        )

        return {
            "total_website_traffic": total_website_traffic,
            "total_ad_spend": round(total_ad_spend, 2),
            "total_ad_conversions": total_ad_conversions,
            "total_organic_clicks": total_organic_clicks,
            "total_new_leads": total_new_leads,
            "total_revenue": round(total_revenue, 2),
            "cost_per_lead": round(cost_per_lead, 2),
            "key_highlights": self._get_key_highlights(),
        }

    def _get_key_highlights(self) -> list[str]:
        """Get key highlights from all data sources.

        Returns:
            List of key highlight strings
        """
        highlights = []

        ga4_analysis = self.analyze_ga4()
        ads_analysis = self.analyze_google_ads()
        sc_analysis = self.analyze_search_console()
        hubspot_analysis = self.analyze_hubspot()

        for analysis in [ga4_analysis, ads_analysis, sc_analysis, hubspot_analysis]:
            insights = analysis.get("insights", [])
            if insights:
                highlights.append(f"[{analysis['source']}] {insights[0]}")

        return highlights
