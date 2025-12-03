"""AI Reporter for generating GA4 reports using OpenAI or Vertex AI."""

import json
import os
from typing import Any

import openai
from google import genai


class AIReporter:
    """Reporter that uses AI to generate GA4 insights and reports."""

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
            self.client = genai.Client(
                vertexai=True,
                project=self.gcp_project_id,
                location=gcp_location,
            )
            self.model_name = os.environ.get("GENAI_MODEL_NAME", "gemini-2.0-flash")
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def generate_report(
        self, analysis_data: dict[str, Any], language: str = "ja"
    ) -> str:
        """Generate a GA4 report from analysis data.

        Args:
            analysis_data: Dictionary containing GA4 KPI analysis
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
            analysis_data: Dictionary containing GA4 KPI analysis
            language: Target language for the report

        Returns:
            Formatted prompt string
        """
        data_json = json.dumps(analysis_data, indent=2, default=str, ensure_ascii=False)

        if language == "ja":
            prompt = f"""あなたはウェブアナリストです。以下のGA4（Google Analytics 4）のKPIデータを分析し、日次レポートを作成してください。

## データ
{data_json}

## レポート要件
1. エグゼクティブサマリー（3-4文で全体の状況を要約）
2. 主要指標の分析
   - ユーザー数・セッション数の推移
   - ページビュー・直帰率
   - コンバージョン・収益（データがある場合）
3. 前日比のトレンド分析
4. 重要なインサイトと推奨アクション
5. 注意が必要な指標（あれば）

## フォーマット
- Slackに投稿するため、マークダウン形式で記述
- 絵文字を適切に使用して読みやすく
- 数値は具体的に記載
- 前日比や週間トレンドがあれば言及

レポートを日本語で作成してください。"""
        else:
            prompt = f"""You are a web analyst. Analyze the following GA4 (Google Analytics 4) KPI data and create a daily report.

## Data
{data_json}

## Report Requirements
1. Executive Summary (summarize the overall situation in 3-4 sentences)
2. Key metrics analysis
   - Users and sessions trends
   - Pageviews and bounce rate
   - Conversions and revenue (if data available)
3. Day-over-day trend analysis
4. Key insights and recommended actions
5. Metrics requiring attention (if any)

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
                    "content": "You are an expert web analyst who creates clear, actionable daily GA4 reports.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.7,
        )

        return response.choices[0].message.content

    def _generate_with_vertexai(self, prompt: str) -> str:
        """Generate report using Vertex AI Gemini via google-genai.

        Args:
            prompt: The prompt for report generation

        Returns:
            Generated report text
        """
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "max_output_tokens": 2000,
                "temperature": 0.7,
            },
        )

        return response.text

    def generate_alert_message(
        self, analysis_data: dict[str, Any], thresholds: dict[str, Any] | None = None
    ) -> str | None:
        """Generate alert message if any GA4 metrics exceed thresholds.

        Args:
            analysis_data: Dictionary containing GA4 KPI analysis
            thresholds: Dictionary of metric thresholds for alerts

        Returns:
            Alert message if thresholds exceeded, None otherwise
        """
        if thresholds is None:
            thresholds = {
                "bounce_rate_max": 80,
                "sessions_min": 100,
            }

        alerts = []

        summary = analysis_data.get("summary", {})
        bounce_rate = summary.get("avg_bounce_rate", 0)
        if bounce_rate > thresholds.get("bounce_rate_max", 80):
            alerts.append(
                f":warning: GA4: 直帰率が高くなっています ({bounce_rate}%)"
            )

        total_sessions = summary.get("total_sessions", 0)
        if total_sessions < thresholds.get("sessions_min", 100):
            alerts.append(
                f":warning: GA4: セッション数が少なくなっています ({total_sessions})"
            )

        if alerts:
            return "\n".join(
                [":rotating_light: *アラート* :rotating_light:", ""] + alerts
            )

        return None
