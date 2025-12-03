"""KPI Analyzer for aggregating and analyzing GA4 and Google Ads metrics."""

from datetime import datetime
from typing import Any


class KPIAnalyzer:
    """Analyzer for GA4 and Google Ads KPIs."""

    def __init__(
        self,
        ga4_data: dict[str, Any],
        google_ads_data: dict[str, Any] | None = None,
    ):
        """Initialize KPI Analyzer.

        Args:
            ga4_data: Dictionary containing GA4 metrics
            google_ads_data: Dictionary containing Google Ads metrics
        """
        self.ga4_data = ga4_data
        self.google_ads_data = google_ads_data or {}
        self.analysis_date = datetime.now().strftime("%Y-%m-%d")

    def analyze(self) -> dict[str, Any]:
        """Analyze all metrics and identify trends.

        Returns:
            Dictionary containing full analysis
        """
        result = {
            "analysis_date": self.analysis_date,
            "ga4": self.analyze_ga4(),
        }

        if self.google_ads_data and not self.google_ads_data.get("error"):
            result["google_ads"] = self.analyze_google_ads()

        return result

    def analyze_ga4(self) -> dict[str, Any]:
        """Analyze GA4 metrics and identify trends.

        Returns:
            Dictionary containing GA4 analysis
        """
        summary = self.ga4_data.get("summary", {})
        daily_data = self.ga4_data.get("daily_data", [])

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
            "analysis_date": self.analysis_date,
            "source": "GA4",
            "period": self.ga4_data.get("period", ""),
            "summary": summary,
            "daily_data": daily_data,
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
        summary = self.google_ads_data.get("summary", {})
        daily_data = self.google_ads_data.get("daily_data", [])

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
            "period": self.google_ads_data.get("period", ""),
            "summary": summary,
            "daily_data": daily_data,
            "trends": {
                "clicks_change_pct": clicks_change,
                "cost_change_pct": cost_change,
                "conversions_change_pct": conversions_change,
            },
            "insights": self._generate_ads_insights(summary),
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

        total_users = summary.get("total_users", 1)
        if total_users > 0:
            new_user_ratio = summary.get("total_new_users", 0) / total_users * 100
            if new_user_ratio > 70:
                insights.append(
                    f"High new user ratio ({new_user_ratio:.1f}%) - good acquisition but focus on retention"
                )

        total_sessions = summary.get("total_sessions", 0)
        total_purchases = summary.get("total_purchases", 0)
        if total_sessions > 0 and total_purchases > 0:
            conversion_rate = total_purchases / total_sessions * 100
            insights.append(f"Conversion rate: {conversion_rate:.2f}%")

        total_revenue = summary.get("total_revenue", 0)
        if total_revenue > 0:
            insights.append(f"Total revenue: ${total_revenue:,.2f}")

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

        total_cost = summary.get("total_cost", 0)
        total_conversions = summary.get("total_conversions", 0)
        if total_cost > 0 and total_conversions > 0:
            cost_per_conversion = total_cost / total_conversions
            insights.append(f"Cost per conversion: ${cost_per_conversion:.2f}")

        return insights
