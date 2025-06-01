# Use the latest Python slim image based on Debian Bullseye
FROM python:3-slim-bullseye

# Set environment variables to prevent Python from writing .pyc files and to buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the application code
COPY . /app/

# Set up cron job
RUN echo "0 0 * * * /usr/local/bin/python /app/manage.py generate_daily_checklists >> /var/log/cron.log 2>&1" > /etc/cron.d/daily_checklists
RUN chmod 0644 /etc/cron.d/daily_checklists
RUN crontab /etc/cron.d/daily_checklists
RUN touch /var/log/cron.log

# Create startup script
RUN echo '#!/bin/bash\nservice cron start\npython manage.py runserver 0.0.0.0:8000' > /app/start.sh
RUN chmod +x /app/start.sh

# Expose port (optional if using docker-compose)
EXPOSE 8000

# Run the startup script
CMD ["/app/start.sh"]
