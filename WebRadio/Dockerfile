FROM python:3.12-slim

# set the working directory in the container
WORKDIR /app/

# copy the content of the local src directory to the working directory
COPY src/webradio_stream.py src/
COPY requirements.txt .

# install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm -f requirements.txt

CMD ["uvicorn", "src.webradio_stream:app", "--host", "0.0.0.0", "--port", "5010", "--timeout-keep-alive", "60"]