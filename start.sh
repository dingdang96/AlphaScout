#!/bin/bash
APP_NAME="AlphaScout"
PID_FILE="app.pid"
PYTHON_CMD="python3"if [ -f "$PID_FILE" ]; then
PID=$(cat "$PID_FILE")
if ps -p $PID > /dev/null 2>&1; then
echo "[!] $APP_NAME 正在运行中，PID: $PID"
exit 1
else
rm -f "$PID_FILE"
fi
fiecho "[*] 启动 $APP_NAME 守护进程..."
nohup $PYTHON_CMD main.py > /dev/null 2>&1 &
PID=$!echo $PID > "$PID_FILE"
echo "[+] 服务启动成功！后台 PID: $PID"
echo "[+] 日志文件: ./logs/app.log"