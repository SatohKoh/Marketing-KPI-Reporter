# GA4 KPI Reporter

BigQueryのGA4（Google Analytics 4）データを分析し、毎日のKPIをSlackに通知するPythonスクリプトです。

## 機能

- **BigQuery連携**: GA4のデータを取得
- **日付パーティション最適化**: 直近7日間のデータのみスキャンしてコスト削減
- **AI レポート生成**: OpenAI GPT-4 または Vertex AI Gemini でレポートテキストを自動生成
- **Slack通知**: 日次レポートとアラートをSlackチャンネルに送信
- **Cloud Functions対応**: Google Cloud Functionsにデプロイ可能

## アーキテクチャ

```
Cloud Scheduler → Pub/Sub → Cloud Functions
                                    ↓
                              BigQuery (GA4)
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
- BigQuery に GA4 (Google Analytics 4) データがエクスポートされていること
- Slack Webhook URL または Bot Token
- OpenAI API Key (OpenAI使用時) または Vertex AI API有効化 (Gemini使用時)

### 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `GCP_PROJECT_ID` | Yes | GCPプロジェクトID |
| `GA4_DATASET` | Yes | GA4データセット名 (例: `analytics_123456789`) |
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
gcloud functions deploy ga4-kpi-report \
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
gcloud scheduler jobs create http ga4-kpi-daily \
    --schedule="0 9 * * *" \
    --time-zone="Asia/Tokyo" \
    --uri="https://REGION-PROJECT_ID.cloudfunctions.net/ga4-kpi-report" \
    --http-method=POST \
    --location=us-central1
```

## BigQueryデータセット構成

### GA4
- テーブル: `events_*` (日付シャード)
- パーティション: `_TABLE_SUFFIX`

## KPI指標

### GA4
- ユーザー数、セッション数、ページビュー
- 新規ユーザー、直帰率
- コンバージョン、収益

## ファイル構成

```
ga4-kpi-reporter/
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
