#!/bin/bash

echo "启动后端服务..."
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "后端服务已启动，PID: $BACKEND_PID"
echo "后端 API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
wait $BACKEND_PID
