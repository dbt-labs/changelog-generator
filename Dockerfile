FROM python:3.11.0a2-alpine

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
ENTRYPOINT ["/usr/src/app/src/main.py"]
