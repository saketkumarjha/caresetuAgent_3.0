FROM python:3.11.9-slim

WORKDIR /app

# Copy and install dependencies first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only essential application files (NOT everything)
COPY src/ ./src/
COPY config/ ./config/
COPY integrations/ ./integrations/
COPY .env .

# Set working directory to where your agent.py is located
WORKDIR /app/src

# Run your agent
CMD ["python", "agent.py"]
