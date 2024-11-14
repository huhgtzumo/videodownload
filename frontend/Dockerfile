FROM node:16-alpine

WORKDIR /app

ENV NPM_CONFIG_LOGLEVEL verbose

COPY package*.json ./
RUN npm install --no-optional --max-attempts=5 --retry=3

COPY . .

EXPOSE 3000

CMD ["npm", "start"] 