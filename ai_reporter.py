"""AI Reporter for generating marketing reports using OpenAI or Vertex AI."""

import json
import os
from typing import Any

import openai
import vertexai
from vertexai.generative_models import GenerativeModel


class AIReporter:
    """Reporter that uses AI to generate marketing insights and reports."""

    def __init__(
        self,
        provider: str = "openai",
        openai_api_key: str | None = None,
        gcp_project_id: str | None = None,
        gcp_location: str = "us-central1",
    ):
        """Initialize AI Reporter.

        Args:
            provider: AI provider to use ('openai' or 'vertexai')
            openai_api_key: OpenAI API key (required if provider is 'openai')
            gcp_project_id: GCP project ID (required if provider is 'vertexai')
            gcp_location: GCP location for Vertex AI
        """
        self.provider = provider.lower()

        if self.provider == "openai":
            self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
            if not self.openai_api_key:
                raise ValueError("OpenAI API key is required for OpenAI provider")
            self.client = openai.OpenAI(api_key=self.openai_api_key)
        elif self.provider == "vertexai":
            self.gcp_project_id = gcp_project_id or os.environ.get("GCP_PROJECT_ID")
            if not self.gcp_project_id:
                raise ValueError("GCP project ID is required for Vertex AI provider")
            vertexai.init(project=self.gcp_project_id, location=gcp_location)
            self.model = GenerativeModel("gemini-1.5-pro")
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def generate_report(
        self, analysis_data: dict[str, Any], language: str = "ja"
    ) -> str:
        """Generate a marketing report from analysis data.

        Args:
            analysis_data: Dictionary containing KPI analysis from all sources
            language: Language for the report ('ja' for Japanese, 'en' for English)

        Returns:
            Generated report text
        """
        prompt = self._build_prompt(analysis_data, language)

        if self.provider == "openai":
            return self._generate_with_openai(prompt)
        else:
            return self._generate_with_vertexai(prompt)

    def _build_prompt(self, analysis_data: dict[str, Any], language: str) -> str:
        """Build the prompt for AI report generation.

        Args:
            analysis_data: Dictionary containing KPI analysis
            language: Target language for the report

        Returns:
            Formatted prompt string
        """
        data_json = json.dumps(analysis_data, indent=2, default=str, ensure_ascii=False)

        if language == "ja":
            prompt = f"""あなたはマーケティングアナリストです。以下のマーケティングKPIデータを分析し、日次レポートを作成してください。

## データ
{data_json}

## レポート要件
1. エグゼクティブサマリー（3-4文で全体の状況を要約）
2. 各チャネルのパフォーマンス分析
   - GA4（ウェブサイトトラフィック）
   - Google Ads（広告パフォーマンス）
   - Search Console（SEOパフォーマンス）
   - HubSpot（リード獲得・CRM）
3. 重要なインサイトと推奨アクション
4. 注意が必要な指標（あれば）

## フォーマット
- Slackに投稿するため、マークダウン形式で記述
- 絵文字を適切に使用して読みやすく
- 数値は具体的に記載
- 前日比や週間トレンドがあれば言及

レポートを日本語で作成してください。"""
        else:
            prompt = f"""You are a marketing analyst. Analyze the following marketing KPI data and create a daily report.

## Data
{data_json}

## Report Requirements
1. Executive Summary (summarize the overall situation in 3-4 sentences)
2. Performance analysis for each channel
   - GA4 (Website Traffic)
   - Google Ads (Advertising Performance)
   - Search Console (SEO Performance)
   - HubSpot (Lead Generation & CRM)
3. Key insights and recommended actions
4. Metrics requiring attention (if any)

## Format
- Use markdown format for Slack posting
- Use appropriate emojis for readability
- Include specific numbers
- Mention day-over-day or weekly trends if available

Please create the report in English."""

        return prompt

    def _generate_with_openai(self, prompt: str) -> str:
        """Generate report using OpenAI GPT-4.

        Args:
            prompt: The prompt for report generation

        Returns:
            Generated report text
        """
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert marketing analyst who creates clear, actionable daily reports for marketing teams.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.7,
        )

        return response.choices[0].message.content

    def _generate_with_vertexai(self, prompt: str) -> str:
        """Generate report using Vertex AI Gemini.

        Args:
            prompt: The prompt for report generation

        Returns:
            Generated report text
        """
        response = self.model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 2000,
                "temperature": 0.7,
            },
        )

        return response.text

    def generate_alert_message(
        self, analysis_data: dict[str, Any], thresholds: dict[str, Any] | None = None
    ) -> str | None:
        """Generate alert message if any metrics exceed thresholds.

        Args:
            analysis_data: Dictionary containing KPI analysis
            thresholds: Dictionary of metric thresholds for alerts

        Returns:
            Alert message if thresholds exceeded, None otherwise
        """
        if thresholds is None:
            thresholds = {
                "bounce_rate_max": 80,
                "ctr_min": 1,
                "roas_min": 1,
                "avg_position_max": 30,
            }

        alerts = []

        ga4_summary = analysis_data.get("ga4", {}).get("summary", {})
        bounce_rate = ga4_summary.get("avg_bounce_rate", 0)
        if bounce_rate > thresholds.get("bounce_rate_max", 80):
            alerts.append(
                f":warning: GA4: 直帰率が高くなっています ({bounce_rate}%)"
            )

        ads_summary = analysis_data.get("google_ads", {}).get("summary", {})
        ctr = ads_summary.get("avg_ctr", 0)
        if ctr < thresholds.get("ctr_min", 1):
            alerts.append(f":warning: Google Ads: CTRが低下しています ({ctr}%)")

        roas = ads_summary.get("roas", 0)
        if roas < thresholds.get("roas_min", 1):
            alerts.append(
                f":rotating_light: Google Ads: ROASが1を下回っています ({roas})"
            )

        sc_summary = analysis_data.get("search_console", {}).get("summary", {})
        avg_position = sc_summary.get("avg_position", 0)
        if avg_position > thresholds.get("avg_position_max", 30):
            alerts.append(
                f":warning: Search Console: 平均掲載順位が低下しています ({avg_position})"
            )

        if alerts:
            return "\n".join(
                [":rotating_light: *アラート* :rotating_light:", ""] + alerts
            )

        return None
