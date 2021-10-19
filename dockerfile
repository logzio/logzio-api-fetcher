FROM python:3.9
WORKDIR /app
COPY /src ./src
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "-m", "src.main"]