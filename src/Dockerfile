FROM python:3.10

EXPOSE 8080

WORKDIR /code

COPY requirements.txt requirements.txt
RUN apt-get update
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python", "start.py", "console"]
