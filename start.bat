@echo off
echo Starting AI Unit Test Generator...

cd backend\app
start cmd /k "python run.py"

cd ..\..\frontend
start cmd /k "npm start"

echo Services started!
echo Backend running at http://localhost:8888
echo Frontend running at http://localhost:3000
echo.
echo Press any key to exit this window (services will continue running)
pause > nul
