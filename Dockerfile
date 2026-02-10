FROM mcr.microsoft.com/playwright/python:latest

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY whistleblower.py /app/whistleblower.py
COPY sites /app/sites
COPY data /app/data

ENTRYPOINT ["python", "/app/whistleblower.py"]
