# Windows 會議室電腦安裝指南

> 只需要安裝一次，之後更新只要執行 `update.bat`。

---

## 事前準備

- Windows 10 以上
- 穩定的網路連線
- 備好兩組 API Key：
  - **Anthropic API Key**（已有，向 Leo 取得）
  - **OpenAI API Key**（向 Leo 取得）

---

## 步驟一：安裝 Python

1. 開啟瀏覽器，前往 https://www.python.org/downloads/
2. 點「Download Python 3.11.x」
3. 執行安裝程式，**務必勾選「Add Python to PATH」**
4. 安裝完成後，開啟「命令提示字元」，輸入：
   ```
   python --version
   ```
   看到版本號代表成功。

---

## 步驟二：安裝 Git

1. 前往 https://git-scm.com/download/win
2. 下載並安裝（全部選預設值即可）
3. 安裝完成後，在命令提示字元輸入：
   ```
   git --version
   ```
   看到版本號代表成功。

---

## 步驟三：下載系統

開啟「命令提示字元」，輸入以下指令：

```
cd C:\Users\Public
git clone https://github.com/LeoHsu625/altra-meeting-advisor.git
cd altra-meeting-advisor
```

---

## 步驟四：安裝套件

在命令提示字元輸入：

```
pip install -r requirements.txt
pip install openai
```

---

## 步驟五：設定 API Key

在 `altra-meeting-advisor` 資料夾內，新增一個檔案名為 `.env`，內容如下：

```
ANTHROPIC_API_KEY=（向 Leo 取得）
OPENAI_API_KEY=（向 Leo 取得）
WHISPER_BACKEND=openai
```

> 設定方式：在資料夾空白處按右鍵 → 新增文字文件 → 命名為 `.env` → 用記事本填入以上內容。

---

## 步驟六：啟動系統

雙擊資料夾內的 **`start.bat`**，看到以下訊息代表成功：

```
系統啟動中，請稍候...
啟動後請用瀏覽器開啟：http://localhost:8000
```

用瀏覽器開啟 `http://localhost:8000`，看到會議顧問介面即完成。

---

## 日後更新（有新版本時）

雙擊 **`update.bat`** 即可自動更新到最新版本。

---

## 常見問題

| 問題 | 解法 |
|---|---|
| 網頁打不開 | 確認 `start.bat` 視窗還開著，沒有錯誤訊息 |
| 看到「pip 不是指令」 | 重新安裝 Python，確認有勾選「Add to PATH」 |
| 看到「git 不是指令」 | 重新安裝 Git |
| AI 沒有回應 | 確認 `.env` 裡的 API Key 是否填正確 |

---

有問題請聯繫 Leo（內分機 / Line）。
