FROM python:3.9.13-slim

WORKDIR /app

COPY requirements.txt .


RUN python -m pip install --upgrade pip setuptools wheel

RUN pip install \
    --no-cache-dir \
    --default-timeout=300 \
    --retries=10 \
    -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]