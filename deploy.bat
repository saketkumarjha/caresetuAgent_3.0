@echo off
echo CareSetu Voice Agent Deployment Helper
echo =====================================

echo Building Docker image...
docker build -t caresetu-voice-agent .

echo Starting the agent...
docker run -p 8081:8081 --env-file .env caresetu-voice-agent

echo Agent is running! Check the logs above for any issues.
echo Press Ctrl+C to stop the agent.