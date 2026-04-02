# Pixeldrain Discord Watch Bot

監視 pixeldrain 共享資料夾的新增 / 刪除 / 更新，並把變更通知送到 Discord。

## 目前功能

- 單一 scheduler loop，不會因為監視目標變多就一直開新 loop
- SQLite 儲存 watch 設定與快照
- 啟動時可自動 seed 初始 watch
- 第一次掃描只建立 baseline，不通知
- 遞迴掃描子資料夾
- slash commands：
  - `/watch_add`
  - `/watch_list`
  - `/watch_remove`
  - `/watch_enable`
  - `/watch_disable`
  - `/watch_scan`
  - `/watch_help`

## 專案結構

```text
pixeldrain-discord-bot/
├─ bot.py                      # 入口：啟動 bot、同步指令、啟動 watch manager
├─ config.py                   # 讀取 .env 與集中設定
├─ requirements.txt            # Python 套件
├─ .env.example                # 設定範本
├─ data/
│  └─ bot.db                   # SQLite 資料庫
├─ deploy/
│  └─ pixeldrain-bot.service   # systemd 服務檔
└─ src/
   ├─ __init__.py
   ├─ logging_config.py        # logging 設定
   ├─ models.py                # 資料結構
   ├─ db.py                    # 建表與 DB CRUD
   ├─ pixeldrain_client.py     # pixeldrain API、share ID 解析、遞迴掃描
   ├─ diff_engine.py           # 新舊快照比較
   ├─ notifier.py              # Discord embed 格式
   ├─ watch_manager.py         # 單一 scheduler + 手動掃描
   └─ commands/
      ├─ __init__.py
      └─ watch_commands.py     # slash commands
```

## 每個檔案的分工

### `bot.py`
只保留啟動流程。這樣之後改部署方式或換指令同步邏輯，不會影響核心掃描邏輯。

### `pixeldrain_client.py`
專門處理 pixeldrain。這層如果未來 API 行為改了，只要集中改這裡。

### `watch_manager.py`
整個機器人的核心。只開一個排程 loop，定時檢查哪些監視項目到期，然後掃描、比對、通知。

### `db.py`
把資料表與 CRUD 獨立出來，commands 跟 manager 都能重用，不會把 SQL 散得到處都是。

### `notifier.py`
通知格式幾乎一定會一直改，單獨拆出來比較乾淨。

### `watch_commands.py`
slash commands 層只負責收參數、做基本驗證、呼叫 service/db，不碰 HTTP 細節。

## 需求

- Python 3.11+
- 一個 Discord bot token
- 一個 Discord 頻道給通知
- 可讀的 pixeldrain 共享資料夾

## 安裝

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

填好 `.env`：

```env
DISCORD_TOKEN=你的token
DEV_GUILD_ID=你的測試伺服器ID
DEFAULT_CHANNEL_ID=你的通知頻道ID
DATABASE_PATH=./data/bot.db
DEFAULT_INTERVAL_SEC=300
SEED_WATCH_IDS=XXXXXXXX
```

## 啟動

```bash
python bot.py
```

## systemd

把 `deploy/pixeldrain-bot.service` 複製到 `/etc/systemd/system/`，然後：

```bash
sudo systemctl daemon-reload
sudo systemctl enable pixeldrain-bot
sudo systemctl start pixeldrain-bot
sudo systemctl status pixeldrain-bot
```

## 指令範例

```text
/watch_add url:https://pixeldrain.com/d/XXXXXXXX channel:#bot-alerts interval_min:5 label:A片源
/watch_list
/watch_scan watch_id:1
/watch_disable watch_id:2
/watch_enable watch_id:2
/watch_remove watch_id:2
```

## 注意

pixeldrain 官方有公開 filesystem REST API，但目前沒有正式文件，所以這份程式是依據官方文件提到的用法與前端實際行為來實作。未來如果 pixeldrain 改 API，最可能需要調整的是 `src/pixeldrain_client.py`。
