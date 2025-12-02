# Marketing KPI Reporter

BigQueryのGA4、Google Ads、Search Console、HubSpotデータを連携し、毎日のマーケティングKPIを分析してSlackに通知するPythonスクリプトです。

## 機能

- **BigQuery連携**: GA4、Google Ads、Search Console、HubSpotのデータを取得
- **日付パーティション最適化**: 直近7日間のデータのみスキャンしてコスト削減
- **AI レポート生成**: OpenAI GPT-4 または Vertex AI Gemini でレポートテキストを自動生成
- **Slack通知**: 日次レポートとアラートをSlackチャンネルに送信
- **Cloud Functions対応**: Google Cloud Functionsにデプロイ可能

## アーキテクチャ

```
Cloud Scheduler → Pub/Sub → Cloud Functions
                                    ↓
                              BigQuery (GA4, Google Ads, Search Console, HubSpot)
                                    ↓
                              KPI Analysis
                                    ↓
                              AI Report Generation (OpenAI/Vertex AI)
                                    ↓
                              Slack Notification
```

## セットアップ

### 前提条件

- Google Cloud Platform プロジェクト
- BigQuery に以下のデータがエクスポートされていること:
  - GA4 (Google Analytics 4)
  - Google Ads (Data Transfer Service)
  - Search Console
  - HubSpot (Fivetran等でエクスポート)
- Slack Webhook URL または Bot Token
- OpenAI API Key (OpenAI使用時) または Vertex AI API有効化 (Gemini使用時)

### 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `GCP_PROJECT_ID` | Yes | GCPプロジェクトID |
| `GA4_DATASET` | Yes | GA4データセット名 (例: `analytics_123456789`) |
| `GOOGLE_ADS_DATASET` | Yes | Google Adsデータセット名 |
| `SEARCH_CONSOLE_DATASET` | Yes | Search Consoleデータセット名 |
| `HUBSPOT_DATASET` | Yes | HubSpotデータセット名 |
| `AI_PROVIDER` | Yes | AIプロバイダー (`openai` または `vertexai`) |
| `OPENAI_API_KEY` | Conditional | OpenAI APIキー (AI_PROVIDER=openai時に必須) |
| `SLACK_WEBHOOK_URL` | Conditional | Slack Webhook URL |
| `SLACK_BOT_TOKEN` | Conditional | Slack Bot Token (Webhook URLの代替) |
| `SLACK_CHANNEL` | No | Slackチャンネル (デフォルト: `#marketing-reports`) |
| `REPORT_LANGUAGE` | No | レポート言語 (`ja` または `en`、デフォルト: `ja`) |
| `GCP_LOCATION` | No | Vertex AIリージョン (デフォルト: `us-central1`) |

### ローカル実行

```bash
# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
export GCP_PROJECT_ID="your-project-id"
export GA4_DATASET="analytics_123456789"
export GOOGLE_ADS_DATASET="google_ads_transfer"
export SEARCH_CONSOLE_DATASET="searchconsole_data"
export HUBSPOT_DATASET="hubspot_data"
export AI_PROVIDER="openai"
export OPENAI_API_KEY="sk-..."
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export REPORT_LANGUAGE="ja"

# 実行
python main.py
```

### Cloud Functionsへのデプロイ

```bash
# デプロイスクリプト実行
chmod +x deploy.sh
./deploy.sh

# または手動デプロイ
gcloud functions deploy marketing-kpi-report \
    --gen2 \
    --runtime=python311 \
    --region=us-central1 \
    --source=. \
    --entry-point=marketing_kpi_report \
    --trigger-http \
    --memory=512MB \
    --timeout=540s \
    --set-env-vars="GCP_PROJECT_ID=your-project-id,GA4_DATASET=analytics_123456789,..."
```

### Cloud Schedulerでの定期実行

```bash
# 毎日午前9時(JST)に実行
gcloud scheduler jobs create http marketing-kpi-daily \
    --schedule="0 9 * * *" \
    --time-zone="Asia/Tokyo" \
    --uri="https://REGION-PROJECT_ID.cloudfunctions.net/marketing-kpi-report" \
    --http-method=POST \
    --location=us-central1
```

## BigQueryデータセット構成

### GA4
- テーブル: `events_*` (日付シャード)
- パーティション: `_TABLE_SUFFIX`

### Google Ads
- テーブル: `p_ads_CampaignStats_*`
- パーティション: `_PARTITIONDATE`

### Search Console
- テーブル: `searchdata_site_impression`, `searchdata_url_impression`
- パーティション: `data_date`

### HubSpot
- テーブル: `contacts`, `deals`, `email_events`
- パーティション: `createdate`, `timestamp`

## KPI指標

### GA4
- ユーザー数、セッション数、ページビュー
- 新規ユーザー、直帰率
- コンバージョン、収益

### Google Ads
- インプレッション、クリック、CTR
- コスト、CPC、コンバージョン
- ROAS

### Search Console
- インプレッション、クリック、CTR
- 平均掲載順位
- トップクエリ、トップページ

### HubSpot
- 新規コンタクト、リード、MQL、SQL
- 新規商談、パイプライン金額
- メール開封率、クリック率

## ファイル構成

```
marketing-kpi-reporter/
├── main.py              # Cloud Functions エントリーポイント
├── bigquery_client.py   # BigQuery クエリ実行
├── kpi_analyzer.py      # KPI 分析ロジック
├── ai_reporter.py       # AI レポート生成
├── slack_notifier.py    # Slack 通知
├── requirements.txt     # Python 依存関係
├── deploy.sh           # デプロイスクリプト
├── .gcloudignore       # Cloud Functions 除外ファイル
└── README.md           # このファイル
```

## ライセンス

MIT License
