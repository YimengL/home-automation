FROM python:3.11-slim
WORKDIR /app
COPY src/ src/
ENV PYTHONPATH=/app/src
COPY requirements.txt .
RUN pip install -r requirements.txt
ENTRYPOINT ["python3", "-m", "home_automation.main"]
