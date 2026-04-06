# Pixeldrain Discord Watch Bot

這是一個用 `discord.py` 寫的 Discord 機器人，主要用途是：

**監視 Pixeldrain 分享資料夾有沒有更新，然後自動通知到 Discord 頻道。**

如果資料夾裡有：

- 新增檔案
- 刪除檔案
- 檔案被更新

bot 就會幫你發通知。

<br></br>

# 這個 bot 可以做什麼？

目前主要功能有：

- 監視一個或多個 Pixeldrain 資料夾
- 每個監視項目可以指定不同的通知頻道
- 第一次掃描只建立基準，不會一開始就瘋狂洗版
- 支援掃描子資料夾
- 用 SQLite 存資料，不需要另外架資料庫
- 可以用 `systemd` 做成 24 小時常駐

<br></br>

# 目前有的指令

- `/watch_add`  
  新增一個監視資料夾，或更新原本的設定

- `/watch_list`  
  看目前有哪些監視項目

- `/watch_remove`  
  刪除監視項目

- `/watch_enable`  
  啟用監視

- `/watch_disable`  
  暫時停用監視

- `/watch_scan`  
  手動掃描一次

<br></br>

# 專案結構大概長這樣

```text
pixeldrain-discord-bot/
├─ bot.py
├─ config.py
├─ requirements.txt
├─ .env.example
├─ data/
│  └─ bot.db
├─ deploy/
│  └─ pixeldrain-bot.service
└─ src/
   ├─ db.py
   ├─ diff_engine.py
   ├─ logging_config.py
   ├─ models.py
   ├─ notifier.py
   ├─ pixeldrain_client.py
   ├─ watch_manager.py
   └─ commands/
      └─ watch_commands.py
```

<br></br>

# 每個檔案大概是幹嘛的？

### `bot.py`
主程式入口。  
bot 啟動時會從這裡開始。

### `config.py`
讀 `.env` 裡的設定。  
像是 token、資料庫位置、同步模式之類的。

### `src/db.py`
處理 SQLite 資料庫。  
用來存監視清單和快照資料。

### `src/pixeldrain_client.py`
負責去 Pixeldrain 抓資料夾內容。

### `src/diff_engine.py`
把「舊快照」跟「新快照」做比對，找出哪些檔案有變動。

### `src/notifier.py`
把變更整理成 Discord 訊息或 embed。

### `src/watch_manager.py`
定時掃描的核心邏輯在這裡。

### `src/commands/watch_commands.py`
所有 slash commands 都放這裡。

### `data/bot.db`
SQLite 資料庫檔案。

### `deploy/pixeldrain-bot.service`
給 `systemd` 用的 service 檔範本。

<br></br>

# 需要準備什麼？

你至少需要：

- Python 3.11 以上
- 一台可以長時間跑的 Linux 主機  
  （像是 Vultr、GCP、Oracle Cloud 都可以）

<br></br>

# 怎麼安裝？

## 1. 把專案抓下來

如果你是從 GitHub 下載：

```bash
git clone https://github.com/PeanutNeko/pixeldrain-notice-bot.git
cd pixeldrain-discord-bot
```

<br></br>

## 2. 建立虛擬環境

```bash
python3 -m venv .venv
source .venv/bin/activate
```

<br></br>

## 3. 安裝套件

```bash
pip install -U pip
pip install -r requirements.txt
```

<br></br>

# `.env` 要怎麼設？

先把範本複製一份：

```bash
cp .env.example .env
```

然後打開來改：

```bash
nano .env
```

可以先參考這個：

```env
DISCORD_TOKEN=你的DiscordBotToken
COMMAND_SYNC_GLOBAL=true
DEV_GUILD_ID=
DEFAULT_CHANNEL_ID=
DATABASE_PATH=./data/bot.db
DEFAULT_INTERVAL_SEC=300
LOG_LEVEL=INFO
SEED_WATCH_IDS=
HTTP_USER_AGENT=PixeldrainDiscordWatchBot/1.0
```

<br></br>

# 這些設定是什麼意思？

### `DISCORD_TOKEN`
你的 Discord Bot Token。  
這個最重要，填錯 bot 就起不來。

### `COMMAND_SYNC_GLOBAL=true`
讓指令變成全伺服器都能用的全域指令。

### `DEV_GUILD_ID`
如果你只想先在單一伺服器測試，可以填 guild id。  
如果你已經要正式上線，通常可以留空。

### `DEFAULT_CHANNEL_ID`
預設通知頻道。  
如果你打算全部用指令來指定頻道，這個可以留空。

### `DATABASE_PATH`
SQLite 資料庫位置。

### `SEED_WATCH_IDS`
啟動時自動加入的 Pixeldrain 資料夾 ID。  
如果不想自動加入，就留空。

<br></br>

# 本機怎麼測試？

直接跑：

```bash
source .venv/bin/activate
python bot.py
```

如果沒有報錯，bot 就應該會上線。

<br></br>

# Discord 那邊要怎麼設？

邀請 bot 的時候，請確認有這些：

## OAuth2 Scopes
- `bot`
- `applications.commands`

## Bot 權限
- View Channels
- Send Messages
- Embed Links
- Read Message History
- Use Application Commands

<br></br>

# 怎麼開始用？

## 新增一個監視資料夾

```text
/watch_add url:https://pixeldrain.com/d/(pixeldrain資料夾ID) channel:(讓bot發送通知的頻道名稱) interval_min:(多久掃描一次(單位:分鐘)) label:(名稱)
```

## 看目前有哪些監視項目

```text
/watch_list
```

## 手動掃描一次

```text
/watch_scan watch_id:1
```

## 暫時停用

```text
/watch_disable watch_id:1
```

## 重新啟用

```text
/watch_enable watch_id:1
```

## 刪掉監視項目

```text
/watch_remove watch_id:1
```

<br></br>

# 為什麼第一次掃描沒有通知？

這是正常的。

第一次掃描只是在建立 baseline，  
不然 bot 一啟動就會把整個資料夾內容全部當成「新增檔案」洗到 Discord，很吵。

所以設計上：

- **第一次掃描：只記錄，不通知**
- **之後真的有變化：才通知**

<br></br>

# 怎麼做成 24 小時常駐？

如果你是 Linux 主機，可以用 `systemd`。

## 1. 建立 service 檔

```bash
sudo nano /etc/systemd/system/pixeldrain-bot.service
```

貼上這段：

```ini
[Unit]
Description=Pixeldrain Discord Watch Bot
After=network.target

[Service]
Type=simple
User=userID
WorkingDirectory=/home/userID/apps/pixeldrain-discord-bot
ExecStart=/home/userID/apps/pixeldrain-discord-bot/.venv/bin/python /home/userID/apps/pixeldrain-discord-bot/bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> 記得把 `User`、`WorkingDirectory`、`ExecStart` 改成你自己的實際路徑。

## 2. 重新載入 systemd

```bash
sudo systemctl daemon-reload
```

## 3. 啟動 bot

```bash
sudo systemctl start pixeldrain-bot
```

## 4. 設成開機自動啟動

```bash
sudo systemctl enable pixeldrain-bot
```

## 5. 看服務狀態

```bash
sudo systemctl status pixeldrain-bot
```

## 6. 看即時 log

```bash
journalctl -u pixeldrain-bot -f
```

<br></br>

# 平常更新程式怎麼做？

如果你改了程式然後 push 到 GitHub，主機上可以這樣更新：

```bash
cd /home/userID/apps/pixeldrain-discord-bot
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart pixeldrain-bot
```

看一下狀態有沒有正常：

```bash
sudo systemctl status pixeldrain-bot
journalctl -u pixeldrain-bot -n 100 --no-pager
```

<br></br>

# 常見問題

## 1. 指令看不到
先檢查：

- bot 有沒有真的進到伺服器
- 有沒有 `applications.commands`
- 有沒有 `Use Application Commands`
- bot 啟動時有沒有成功 sync commands

如果是 global commands，有時候不會瞬間出現，要稍微等一下。

<br></br>

## 2. `Improper token has been passed`
通常代表 token 有問題。

先檢查：

- `.env` 有沒有真的讀到
- token 有沒有貼錯
- 有沒有多加引號
- 有沒有寫成 `Bot xxxxxx`

正確格式應該是：

```env
DISCORD_TOKEN=(72碼token)
```

<br></br>

## 3. systemd 啟動失敗
先不要亂猜，直接看 log：

```bash
journalctl -u pixeldrain-bot -n 100 --no-pager
```

常見原因有：

- `.env` 不在專案根目錄
- service 裡的路徑寫錯
- `.venv` 不存在
- 程式本身還有 bug

<br></br>

## 4. 為什麼明明手動能跑，systemd 卻不能跑？
通常是因為：

- `WorkingDirectory` 寫錯
- `ExecStart` 寫錯
- `.env` 沒被讀到
- systemd 的執行使用者不是你以為的那個人

<br></br>

# 目前已知 bug

1. 監視對象刪除後，監視 ID 殘留問題  
2. 無法修改已增加的監視對象

<br></br>

# 未來追加可能

- 更漂亮的通知
- 只通知特定副檔名
- 管理者限制
- Web 控制面板

<br></br>


# 最後提醒

- Discord Bot Token 不要外流
- 如果你重置了 token，記得主機上的 `.env` 也要一起改
- 如果哪天 Pixeldrain API 行為變了，優先先看 `src/pixeldrain_client.py`

<br></br>

# 更新履歷

- 2026.04.02 Release.
- 2026.04.07 Ver1.1 Bug修正