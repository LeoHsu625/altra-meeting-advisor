#!/bin/bash
# AI 會議顧問 — Mac 更新腳本
# 執行方式：bash update.sh

set -e

echo "======================================"
echo "  AI 會議顧問系統更新"
echo "======================================"

echo ""
echo "▶ 拉取最新程式碼..."
git pull origin main

echo ""
echo "▶ 安裝/更新套件..."
pip install -r requirements.txt -q

echo ""
echo "✅ 更新完成！"
echo ""
echo "啟動系統請執行："
echo "  uvicorn web_app:app --host 0.0.0.0 --port 8000"
