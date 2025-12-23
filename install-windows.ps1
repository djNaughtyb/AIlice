################################################################################
# AIlice Platform - Windows Installer
# PowerShell script for automated installation on Windows
################################################################################

# Requires running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "Please run this script as Administrator!"
    Write-Host "Right-click on PowerShell and select 'Run as Administrator'"
    pause
    exit
}

Write-Host "`n" -ForegroundColor Blue
Write-Host "===============================================================" -ForegroundColor Blue
Write-Host "  AIlice Platform - Windows Installer" -ForegroundColor Blue
Write-Host "===============================================================" -ForegroundColor Blue
Write-Host "`n"

function Print-Status {
    param([string]$Message)
    Write-Host "[*] $Message" -ForegroundColor Blue
}

function Print-Success {
    param([string]$Message)
    Write-Host "[✓] $Message" -ForegroundColor Green
}

function Print-Warning {
    param([string]$Message)
    Write-Host "[!] $Message" -ForegroundColor Yellow
}

function Print-Error {
    param([string]$Message)
    Write-Host "[✗] $Message" -ForegroundColor Red
}

# Check for Chocolatey
Print-Status "Checking for Chocolatey package manager..."
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Print-Warning "Chocolatey not found. Installing..."
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    Print-Success "Chocolatey installed"
} else {
    Print-Success "Chocolatey found"
}

# Refresh environment variables
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Install Python
Print-Status "Checking Python installation..."
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Print-Warning "Python not found. Installing Python 3.11..."
    choco install python311 -y
    Print-Success "Python installed"
} else {
    $pythonVersion = python --version
    Print-Success "Python found: $pythonVersion"
}

# Refresh PATH again after Python installation
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Install PostgreSQL
Print-Status "Checking PostgreSQL installation..."
if (!(Get-Command psql -ErrorAction SilentlyContinue)) {
    Print-Warning "PostgreSQL not found. Installing..."
    choco install postgresql15 -y --params '/Password:postgres123'
    Print-Success "PostgreSQL installed"
    $dbPassword = "postgres123"
} else {
    Print-Success "PostgreSQL found"
    $dbPassword = Read-Host "Enter PostgreSQL postgres user password" -AsSecureString
    $dbPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($dbPassword))
}

# Install Git
Print-Status "Checking Git installation..."
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Print-Warning "Git not found. Installing..."
    choco install git -y
    Print-Success "Git installed"
} else {
    Print-Success "Git found"
}

# Refresh PATH again
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Create installation directory
$installDir = "$env:USERPROFILE\AIlice"
Print-Status "Creating installation directory at $installDir..."
New-Item -ItemType Directory -Force -Path $installDir | Out-Null
Set-Location $installDir

# Copy application files
Print-Status "Copying application files..."
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Copy-Item -Path "$scriptDir\*" -Destination $installDir -Recurse -Force -ErrorAction SilentlyContinue

# Create virtual environment
Print-Status "Creating Python virtual environment..."
python -m venv venv
Print-Success "Virtual environment created"

# Activate virtual environment
& "$installDir\venv\Scripts\Activate.ps1"

# Upgrade pip
Print-Status "Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel

# Install dependencies
Print-Status "Installing Python dependencies..."
Print-Warning "This may take several minutes..."

if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    Print-Success "Dependencies installed"
} else {
    Print-Error "requirements.txt not found"
    pause
    exit
}

# Setup PostgreSQL database
Print-Status "Setting up PostgreSQL database..."

# Generate random password for ailice user
$ailicePassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 20 | ForEach-Object {[char]$_})

# Create database and user
$env:PGPASSWORD = $dbPassword

# Create SQL commands file
$sqlCommands = @"
CREATE DATABASE ailice_db;
CREATE USER ailice WITH PASSWORD '$ailicePassword';
GRANT ALL PRIVILEGES ON DATABASE ailice_db TO ailice;
"@

$sqlCommands | Out-File -FilePath "$installDir\setup_db.sql" -Encoding UTF8

# Execute SQL commands
psql -U postgres -f "$installDir\setup_db.sql" 2>$null

Remove-Item "$installDir\setup_db.sql" -ErrorAction SilentlyContinue

Print-Success "Database configured"

# Create .env file
Print-Status "Creating configuration file..."
$envContent = @"
DATABASE_URL=postgresql://ailice:$ailicePassword@localhost:5432/ailice_db
ENVIRONMENT=development
PORT=8080
HOST=127.0.0.1
"@

$envContent | Out-File -FilePath "$installDir\.env" -Encoding UTF8
Print-Success "Configuration file created"

# Create launch scripts
Print-Status "Creating launch scripts..."

# Start script
$startScript = @'
@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
start "AIlice Platform" python fastapi_app.py
echo AIlice Platform is starting...
echo Access it at http://localhost:8080
ping 127.0.0.1 -n 3 > nul
start http://localhost:8080/admin/dashboard
'@

$startScript | Out-File -FilePath "$installDir\start_ailice.bat" -Encoding ASCII

# Stop script
$stopScript = @'
@echo off
echo Stopping AIlice Platform...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq AIlice Platform"
echo AIlice Platform stopped.
pause
'@

$stopScript | Out-File -FilePath "$installDir\stop_ailice.bat" -Encoding ASCII

Print-Success "Launch scripts created"

# Create desktop shortcut
Print-Status "Creating desktop shortcut..."
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\AIlice Platform.lnk")
$Shortcut.TargetPath = "$installDir\start_ailice.bat"
$Shortcut.WorkingDirectory = $installDir
$Shortcut.Description = "AIlice Platform"
$Shortcut.Save()
Print-Success "Desktop shortcut created"

# Create Windows service (optional)
Print-Status "Setting up Windows service (optional)..."
$createService = Read-Host "Do you want to create a Windows service for auto-start? (y/n)"

if ($createService -eq 'y' -or $createService -eq 'Y') {
    # Install NSSM (Non-Sucking Service Manager)
    Print-Status "Installing NSSM..."
    choco install nssm -y
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    # Create service
    $pythonPath = "$installDir\venv\Scripts\python.exe"
    $appPath = "$installDir\fastapi_app.py"
    
    nssm install AIlicePlatform $pythonPath $appPath
    nssm set AIlicePlatform AppDirectory $installDir
    nssm set AIlicePlatform DisplayName "AIlice Platform"
    nssm set AIlicePlatform Description "AIlice AI Agent Platform"
    nssm set AIlicePlatform Start SERVICE_AUTO_START
    
    Print-Success "Windows service created"
    
    $startServiceNow = Read-Host "Start the service now? (y/n)"
    if ($startServiceNow -eq 'y' -or $startServiceNow -eq 'Y') {
        nssm start AIlicePlatform
        Print-Success "Service started"
    }
} else {
    # Start manually
    Print-Status "Starting AIlice Platform..."
    Start-Process -FilePath "$installDir\start_ailice.bat" -WorkingDirectory $installDir
    Start-Sleep -Seconds 5
}

# Display completion message
Write-Host "`n" -ForegroundColor Green
Write-Host "===============================================================" -ForegroundColor Green
Write-Host "         Installation Successful!" -ForegroundColor Green
Write-Host "===============================================================" -ForegroundColor Green
Write-Host "`n"

Write-Host "Access your AIlice platform at:" -ForegroundColor Blue
Write-Host "  • Home: http://localhost:8080" -ForegroundColor Cyan
Write-Host "  • Admin Dashboard: http://localhost:8080/admin/dashboard" -ForegroundColor Cyan
Write-Host "  • API Docs: http://localhost:8080/docs" -ForegroundColor Cyan
Write-Host "`n"

Write-Host "Installation Directory: $installDir" -ForegroundColor Blue
Write-Host "`n"

Write-Host "Database Info:" -ForegroundColor Blue
Write-Host "  Host: localhost" -ForegroundColor Cyan
Write-Host "  Database: ailice_db" -ForegroundColor Cyan
Write-Host "  User: ailice" -ForegroundColor Cyan
Write-Host "  Password: $ailicePassword" -ForegroundColor Cyan
Write-Host "  ⚠ Save this password securely!" -ForegroundColor Yellow
Write-Host "`n"

Write-Host "Useful commands:" -ForegroundColor Blue
Write-Host "  Start AIlice: Run start_ailice.bat (or use desktop shortcut)" -ForegroundColor Cyan
Write-Host "  Stop AIlice: Run stop_ailice.bat" -ForegroundColor Cyan
Write-Host "`n"

$openBrowser = Read-Host "Open admin dashboard in browser now? (y/n)"
if ($openBrowser -eq 'y' -or $openBrowser -eq 'Y') {
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:8080/admin/dashboard"
}

Print-Success "Setup complete! Enjoy using AIlice."
Write-Host "`n"
pause
