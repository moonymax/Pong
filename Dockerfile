FROM python:3.9.16-slim-bullseye
RUN apt update -y && apt upgrade -y
RUN apt install -y ffmpeg

#WORKDIR /usr/src/app
COPY r.txt ./
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r r.txt

COPY . .

CMD [ "python3", "./main.py"]