#!/bin/bash

PID_FILE="app.pid"

if [ ! -f "$PID_FILE" ]; then
echo "[!] PID 文件不存在，服务可能未运行。"
exit 1
fi

PID=$(cat "$PID_FILE")

if ps -p $PID > /dev/null 2>&1; then
echo "[*] 正在停止 PID $PID ..."
kill -15 $PID
sleep 2

if ps -p $PID > /dev/null 2>&1; then
    echo "[*] 进程未及时退出，强行 Kill..."
    kill -9 $PID
fi
echo "[+] 服务已停止。"


else
echo "[!] PID $PID 不存在。"
fi

rm -f "$PID_FILE"