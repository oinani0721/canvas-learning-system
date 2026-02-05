@echo off
chcp 65001 >nul
echo ══════════════════════════════════════════════════════════
echo   Canvas Learning System - 一键启动所有服务
echo ══════════════════════════════════════════════════════════
echo.

:: 从 backend/.env 读取 Neo4j 密码
set NEO4J_PASSWORD=
for /f "tokens=1,* delims==" %%a in ('findstr /B "NEO4J_PASSWORD" "%~dp0backend\.env" 2^>nul') do set NEO4J_PASSWORD=%%b
if "%NEO4J_PASSWORD%"=="" (
    echo [错误] 无法从 backend\.env 读取 NEO4J_PASSWORD
    echo        请确保 backend\.env 文件存在且包含 NEO4J_PASSWORD=your_password
    pause
    exit /b 1
)

:: 1. 启动 Neo4j Docker 容器
echo [1/3] 启动 Neo4j Docker 容器 (canvas-neo4j)...
docker start canvas-neo4j 2>nul
if %errorlevel% equ 0 (
    echo       ✓ canvas-neo4j 已启动 (端口 7687)
) else (
    echo       ! canvas-neo4j 启动失败，尝试创建...
    docker-compose up -d neo4j
)

:: 等待 Neo4j 完全启动
echo       等待 Neo4j 初始化 (10秒)...
timeout /t 10 /nobreak >nul

:: 2. 验证 Neo4j 连接
echo.
echo [2/3] 验证 Neo4j 连接...
docker exec canvas-neo4j cypher-shell -u neo4j -p %NEO4J_PASSWORD% "RETURN 'OK' AS status" 2>nul
if %errorlevel% equ 0 (
    echo       ✓ Neo4j 连接正常
) else (
    echo       ✗ Neo4j 连接失败，请检查密码配置
)

:: 3. 启动后端服务
echo.
echo [3/3] 启动后端 API 服务...
echo       后端将在新窗口中启动...
echo.
start "Canvas Backend" cmd /k "cd /d %~dp0backend && uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo ══════════════════════════════════════════════════════════
echo   启动完成！
echo.
echo   Neo4j Browser:  http://localhost:7474
echo   后端 API:       http://localhost:8000
echo   API 文档:       http://localhost:8000/docs
echo.
echo   在 Obsidian 中点击「刷新状态」验证连接
echo ══════════════════════════════════════════════════════════
pause
