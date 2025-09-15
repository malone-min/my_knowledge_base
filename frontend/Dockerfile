# --- Stage 1: Build ---
FROM node:20 AS build

WORKDIR /app

# 复制 package.json 和 lock 文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制所有源代码
COPY . .

# 构建生产版本的静态文件
RUN npm run build

# --- Stage 2: Serve ---
FROM nginx:stable

# 将构建好的静态文件从 build 阶段复制到 Nginx 的 www 目录
COPY --from=build /app/dist /usr/share/nginx/html

# 复制自定义的 Nginx 配置文件
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露 80 端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]