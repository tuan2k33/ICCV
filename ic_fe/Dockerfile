FROM node:22-alpine AS builder
WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY . .
# Xóa VITE_API_URL để axiosInstance dùng URL tương đối, nginx proxy xử lý
RUN echo "VITE_API_URL=" > .env.production && yarn build

FROM nginx:1.19-alpine AS server

RUN apk add --no-cache gettext

COPY ./build/nginx.conf /etc/nginx/conf.d/nginx.conf.template
COPY --from=builder /app/build/client /usr/share/nginx/html

CMD ["/bin/sh", "-c", "envsubst '${BACKEND_URL}' < /etc/nginx/conf.d/nginx.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
