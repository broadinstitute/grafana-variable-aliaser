FROM us.gcr.io/broad-dsp-gcr-public/base/python:debian
RUN apt-get update \
    && apt-get -y install libpq-dev gcc
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
ENTRYPOINT ["python", "main.py"]