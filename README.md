

## 依赖
python 版本 3.8.10  
django 4.2
mysql 8 

#### 框架
- [django4.2](https://github.com/django/django) 
- [Bootstrap 4.6](https://github.com/twbs/bootstrap)
- [jQuery 3.5.1+](https://github.com/jquery/jquery)


#### 前端组件

- 主题  [adminlte]
- 表格 bootstrap-table
- 时间选择 bootstrap-datetimepicker https://github.com/dangrossman/daterangepicker/

#### 服务器端

- 队列任务 [django_q](https://github.com/Koed00/django-q)
- MySQL Connector mysqlclient-python
- Redis Connector redis-py
- api接口 djangorestframework
- api 接口过滤 django-filter
- drf-jwt  [jwt认证](https://styria-digital.github.io/django-rest-framework-jwt)
- paramiko  ssh私钥处理
- django-cors-headers 跨域处理
- django-mptt 存储树 

#### 功能依赖
- 数据加密 django-mirage-field
- 地理位置 django-geoposition-2
- 加密解密  cryptography[mirage]
- 从.env文件读取为环境变量  django-environ


#### 部署
1、部署mysql和redis （略）

2、设置变量文件连接db和redis
```shell
mv .env.template  .env
# 配置数据库和 redis
DATABASE_URL="mysql://root:123456@192.168.1.1:3306/mp_new"
# cache
CACHE_URL="redis://:123456@192.168.1.1:6379/0"
```
3、设置日志
```shell
cp logs.ini.template logs.ini
```
4、启动
```shell
docker-compose up -d 
```
