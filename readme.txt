# 1. 拉取后端需要的 Python 镜像 (虽然它之前成功了，但我们为了保险起见)
docker pull python:3.11-slim

# 2. 拉取前端构建阶段需要的 Node 镜像
docker pull node:20

# 3. 拉取前端服务阶段需要的 Nginx 镜像
docker pull nginx:stable

这三个可能要单独拉
docker-compose up -d 初次安装用这个命令。
docker-compose up -d --force-recreate 修改配置后运行这个命令。

http://localhost:8888/docs
http://localhost:8080/
运行上面两个地址看看是否显示正常。