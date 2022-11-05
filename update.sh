#!/bin/sh

# 编译静态资源(到相对目录)
cd $(dirname $0)

pyinstaller main.py

# 复制静态资源到相对目录
cp -r dist/main/* .

# 打包上传以提高上传效率
zip -r dist.zip dist/*
scp -r dist.zip root@116.62.124.43:~/dist.zip

ssh root@116.62.124.43 "cd ~/; unzip -o -d ~/ dist.zip; pm2 reload dist; rm dist.zip;"
rm dist.zip

# 修改 nginx 配置(并重启)
#vim /usr/local/nginx/conf/nginx.conf
#/usr/local/nginx/sbin/nginx -s reload
