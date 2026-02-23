@echo off
echo Installing dependencies for Resume AI Project...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js is not installed. Attempting to install Node.js...
    REM Try to install using winget (Windows Package Manager)
    winget install OpenJS.NodeJS --accept-source-agreements --accept-package-agreements >nul 2>&1
    if %errorlevel% neq 0 (
        echo Failed to install Node.js automatically. Please install Node.js manually from https://nodejs.org/
        pause
        exit /b 1
    )
    echo Node.js installed successfully.
)

REM Check if yarn is installed
yarn --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Yarn is not installed. Installing Yarn...
    npm install -g yarn
)

REM Install backend dependencies
echo Installing backend dependencies...
cd backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install backend dependencies.
    pause
    exit /b 1
)
cd ..

REM Install frontend dependencies
echo Installing frontend dependencies...
cd frontend
yarn install
if %errorlevel% neq 0 (
    echo Failed to install frontend dependencies.
    pause
    exit /b 1
)
cd ..

echo All dependencies installed successfully!
pause
