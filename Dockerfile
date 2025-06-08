FROM node:lts-alpine3.22

RUN apk add --no-cache ffmpeg git

#WORKDIR /usr/src/app
COPY . .

RUN npm install

CMD [ "npm", "start"]
