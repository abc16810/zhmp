





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

#### 参考
    OpsManage
    https://github.com/open-cmdb/cmdb
    https://demo.archerydms.com/dashboard/
    https://github.com/guohongze/adminset/wiki/AdminSet
    https://demo.improvely.com/project/webshop
    https://github.com/wylok/sparrow
    
    
#### 审核流程
等待审核-> 审核通过 -> 执行中 -> 正常结束
        - 业务类型为自动更新资产信息（0） 管理员和申请人可以 -> 定时执行 ->正常结束  
        - 其他业务类型  (管理员)认领
                   -> 执行异常 -> 终止流程  (自动)
                   -> 定时执行 ->正常结束   (自动)
                              -> 执行异常 -> 终止流程   (自动)
        -> 审核不通过 -> 终止流程  （自动）
        > 终止流程  (审核人终止)
        
等待审核的管理员/审核人/申请人可终止
其他状态管理员可终止


管理员和权限组中的人员可以审核
业务中的成员可以提交改业务下的工单