from config.env import env

# django q
Q_CLUSTER = {
    'name': 'app',
    'workers': 4,
    'recycle': 500,
    'timeout': 60,
    'compress': True,
    'cpu_affinity': 1,
    'save_limit': 0,
    'queue_limit': 50,
    'label': 'Django Q',
    'redis': env('CACHE_URL'),
    'sync': False  # 本地调试可以修改为True，使用同步模式
}
