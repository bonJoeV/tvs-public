FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY lead_sheets_monitor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY lead_sheets_monitor/monitor.py .

# Create directory for tracker persistence
RUN mkdir -p /data

# Set default environment variables
ENV SENT_TRACKER_FILE=/data/sent_entries.json

# Run the monitor
CMD ["python", "monitor.py"]
