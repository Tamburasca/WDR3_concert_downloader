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

# command to run on container start
# python [-u] forces the stdout and stderr streams to be unbuffered.
CMD ["python3", "-u", "src/webradio_stream.py"]