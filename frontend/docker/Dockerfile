FROM node:16 as react-build   

COPY ./app /app
WORKDIR /app

RUN yarn
RUN yarn build

FROM nginx:alpine
COPY --from=react-build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf