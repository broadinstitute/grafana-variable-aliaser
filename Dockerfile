FROM us.gcr.io/broad-dsp-gcr-public/base/python:debian
RUN apt-get update \
    # Need to compile psycopg2
    && apt-get -y install libpq-dev gcc \
    # Need to pkill
    && apt-get -y install sudo procps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
ENTRYPOINT ["python", "main.py"]