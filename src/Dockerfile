FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
ENV WORKERS=4
ENV THREADS=1

CMD exec functions-framework \
    --target=process_new_csv \
    --signature-type=cloudevent \
    --port=$PORT
