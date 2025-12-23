@echo off
REM ############################################################################
REM AIlice Platform - Windows Quick Installer
REM One-command installation for Windows
REM ############################################################################

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ========================================================
    echo ERROR: This script requires Administrator privileges
    echo ========================================================
    echo.
    echo Please right-click this file and select "Run as Administrator"
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo          AIlice Platform Quick Installer for Windows
echo ================================================================
echo.

echo Choose Installation Method:
echo.
echo 1. Docker Compose (Recommended - Easiest)
echo 2. Native Installation (Full control)
echo 3. Manual Setup Instructions
echo.
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" goto docker_install
if "%choice%"=="2" goto native_install
if "%choice%"=="3" goto manual_instructions

echo Invalid choice. Please run the script again.
pause
exit /b 1

:docker_install
echo.
echo ================================================================
echo              Docker Compose Installation
echo ================================================================
echo.

REM Check for Docker Desktop
where docker >nul 2>&1
if %errorLevel% neq 0 (
    echo Docker Desktop is not installed.
    echo Please download and install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop
    echo.
    set /p continue="Press Enter after installing Docker Desktop..."
)

REM Check if docker-compose exists
where docker-compose >nul 2>&1
if %errorLevel% neq 0 (
    echo docker-compose is not available.
    echo Please ensure Docker Desktop is properly installed and running.
    pause
    exit /b 1
)

echo Starting Docker Compose setup...
echo.

REM Create .env if it doesn't exist
if not exist .env (
    if exist .env.example (
        copy .env.example .env
        echo Created .env file from template.
    ) else (
        echo DB_PASSWORD=changeme123 > .env
        echo DATABASE_URL=postgresql://ailice:changeme123@postgres:5432/ailice_db >> .env
        echo ENVIRONMENT=production >> .env
        echo PORT=8080 >> .env
        echo HOST=0.0.0.0 >> .env
        echo CORS_ORIGINS=* >> .env
        echo Created minimal .env file.
    )
)

echo Pulling Docker images...
docker-compose pull

echo Building application...
docker-compose build

echo Starting services...
docker-compose up -d

echo.
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo.
echo ================================================================
echo            AIlice Platform is now running!
echo ================================================================
echo.
echo Access your platform at:
echo   * Home: http://localhost:8080
echo   * Admin Dashboard: http://localhost:8080/admin/dashboard
echo   * API Docs: http://localhost:8080/docs
echo.
echo Useful commands:
echo   View logs: docker-compose logs -f
echo   Stop services: docker-compose down
echo   Restart: docker-compose restart
echo.

set /p open_browser="Open admin dashboard in browser? (y/n): "
if /i "%open_browser%"=="y" start http://localhost:8080/admin/dashboard

goto end

:native_install
echo.
echo ================================================================
echo              Native Installation
echo ================================================================
echo.
echo Starting PowerShell installer...
echo.
powershell -ExecutionPolicy Bypass -File install-windows.ps1
goto end

:manual_instructions
echo.
echo ================================================================
echo              Manual Setup Instructions
echo ================================================================
echo.
echo To manually set up AIlice on Windows:
echo.
echo 1. Install dependencies:
echo    - Python 3.10 or higher (from python.org)
echo    - PostgreSQL 15 or higher (from postgresql.org)
echo    - Git (from git-scm.com)
echo.
echo 2. Create a virtual environment:
echo    python -m venv venv
echo    venv\Scripts\activate
echo.
echo 3. Install Python packages:
echo    pip install -r requirements.txt
echo.
echo 4. Set up PostgreSQL:
echo    createdb ailice_db
echo    createuser ailice -P
echo.
echo 5. Create .env file with:
echo    DATABASE_URL=postgresql://ailice:password@localhost:5432/ailice_db
echo    ENVIRONMENT=development
echo    PORT=8080
echo    HOST=127.0.0.1
echo.
echo 6. Start the application:
echo    python fastapi_app.py
echo.
echo For detailed instructions, see DEPLOYMENT_OPTIONS.md
echo.
goto end

:end
echo.
echo Installation process completed!
echo.
pause
