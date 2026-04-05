FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    git \
    tesseract-ocr \
    tesseract-ocr-deu \
    poppler-utils \
    fonts-symbola \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY src/ src/
ENV PYTHONPATH=/app/src
COPY requirements.txt .
RUN pip install -r requirements.txt


RUN python -m spacy download de_core_news_md \
 && python -m spacy download en_core_web_md

ENTRYPOINT ["python3", "-m", "home_automation.main"]
