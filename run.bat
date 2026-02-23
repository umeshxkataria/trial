@echo off
echo Starting Resume AI Project...

REM Start backend
echo Starting backend server...
start cmd /k "cd backend && python -m pip install -r requirements.txt && python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000"

REM Start frontend
echo Starting frontend...
start cmd /k "cd frontend && yarn install && yarn start"

echo Both backend and frontend are starting...
echo Backend will be available at http://localhost:8000
echo Frontend will be available at http://localhost:3000
pause
