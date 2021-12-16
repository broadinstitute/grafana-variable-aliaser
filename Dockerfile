FROM us.gcr.io/broad-dsp-gcr-public/base/python:debian
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
ENTRYPOINT ["python", "main.py"]