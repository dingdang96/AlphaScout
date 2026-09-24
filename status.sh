#!/bin/bash
PID_FILE="app.pid"
if [ -f "$PID_FILE" ]; then
PID=$(cat "$PID_FILE")
if ps -p $PID > /dev/null 2>&1; then
echo "● AlphaScout 正常运行中 | PID: $PID"
echo "---------------------------------------------------"
echo "最新 10 行运行日志:"
tail -n 10 logs/app.log
echo "---------------------------------------------------"
else
echo "○ 服务未运行 (残留 PID 文件)"
fi
else
echo "○ 服务未运行"
fi