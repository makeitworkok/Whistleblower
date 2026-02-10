FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY whistleblower.py /app/whistleblower.py
COPY sites /app/sites
COPY data /app/data

ENTRYPOINT ["python", "/app/whistleblower.py"]
