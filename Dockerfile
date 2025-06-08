FROM node:lts-alpine3.22

RUN apk add --no-cache ffmpeg

#WORKDIR /usr/src/app
COPY . .

RUN npm install

CMD [ "npm", "start"]
