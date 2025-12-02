"""KPI Analyzer for aggregating and analyzing GA4 metrics."""

from datetime import datetime
from typing import Any


class KPIAnalyzer:
    """Analyzer for GA4 KPIs."""

    def __init__(self, ga4_data: dict[str, Any]):
        """Initialize KPI Analyzer.

        Args:
            ga4_data: Dictionary containing GA4 metrics
        """
        self.ga4_data = ga4_data
        self.analysis_date = datetime.now().strftime("%Y-%m-%d")

    def analyze(self) -> dict[str, Any]:
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
            "insights": self._generate_insights(summary),
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

    def _generate_insights(self, summary: dict[str, Any]) -> list[str]:
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
