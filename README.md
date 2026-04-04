# home-automation

Watches a folder for translated mail PDFs and syncs them to Cloudflare D1, R2, and Telegram.

## Prerequisites

- [Colima](https://github.com/abiosoft/colima) + Docker
- [Doppler](https://doppler.com) CLI configured for project `home-automation / prd`

## Running

```bash
doppler run --project home-automation --config prd -- docker compose up --build
```

## Services

| Service | Image | Role |
|---|---|---|
| `pdf-watch` | `ghcr.io/yimengl/private-pdf-translator:1.0.1` | Watches for `ori_*.pdf`, produces `proc_*.pdf` + `proc_*.json` |
| `json-watch` | local build | Watches for `proc_*.json`, upserts to D1, uploads to R2, sends Telegram notification |

## Secrets (managed via Doppler)

| Env var | Purpose |
|---|---|
| `CF_ACCOUNT_ID` | Cloudflare account ID |
| `CF_D1_DATABASE_ID` | D1 database ID |
| `CLOUDFLARE_HOME_AUTOMATION` | Cloudflare API token (D1 access) |
| `R2_BUCKET_NAME` | R2 bucket name |
| `R2_HOME_AUTOMATION_MAIL_KEY_ID` | R2 S3-compatible access key ID |
| `R2_HOME_AUTOMATION_MAIL_SECRET` | R2 S3-compatible secret key |
| `TG_CHAT_ID` | Telegram chat ID |
| `YM_MAIL_BOT` | Telegram bot token |
| `ANTHROPIC_API_KEY` | Claude API key (for pdf-watch) |
| `DEEPL_API_KEY` | DeepL API key (for pdf-watch) |
