FROM python:3.8-slim-buster

RUN apt-get update
RUN apt-get install pkg-config g++ libpq-dev postgresql libpoppler-cpp-dev -y
RUN apt-get install gfortran libopenblas-dev liblapack-dev -y

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
RUN rm /requirements.txt

COPY ./app /app
WORKDIR /app

CMD ["python","-u", "paper_fetcher.py"]
