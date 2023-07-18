# 自定义验证
CUSTOM_AUTHENTICATION_METHOD = "username_email"   # username_email  email  username
CUSTOM_USERNAME_FIELD = "username"
CUSTOM_USER_MODEL_EMAIL_FIELD = 'email'
CUSTOM_USER_MODEL_USERNAME_FIELD = 'username'
CUSTOM_LOGIN_ATTEMPTS_LIMIT = 5
CUSTOM_LOGIN_ATTEMPTS_TIMEOUT = 60 * 5

# 文件
FILE_UPLOAD_HANDLERS = [
    # "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "config.upload.uploadhandler.MyTemporaryFileUploadHandler",
]
FILE_UPLOAD_MAX_SIZE = 10485760  # 10M
