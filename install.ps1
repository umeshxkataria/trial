Write-Host "Installing dependencies for Resume AI Project..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>$null
    Write-Host "Python is installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python is not installed. Please install Python from https://www.python.org/downloads/" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Node.js is installed
try {
    $nodeVersion = node --version 2>$null
    Write-Host "Node.js is installed: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "Node.js is not installed. Attempting to install Node.js..." -ForegroundColor Yellow
    try {
        winget install OpenJS.NodeJS --accept-source-agreements --accept-package-agreements
        Write-Host "Node.js installed successfully." -ForegroundColor Green
    } catch {
        Write-Host "Failed to install Node.js automatically. Please install Node.js manually from https://nodejs.org/" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Check if yarn is installed
try {
    $yarnVersion = yarn --version 2>$null
    Write-Host "Yarn is installed: $yarnVersion" -ForegroundColor Green
} catch {
    Write-Host "Yarn is not installed. Installing Yarn..." -ForegroundColor Yellow
    npm install -g yarn
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install Yarn." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Install backend dependencies
Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
Set-Location backend
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install backend dependencies." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Set-Location ..

# Install frontend dependencies
Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location frontend
yarn install
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install frontend dependencies." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Set-Location ..

Write-Host "All dependencies installed successfully!" -ForegroundColor Green
Read-Host "Press Enter to exit"
