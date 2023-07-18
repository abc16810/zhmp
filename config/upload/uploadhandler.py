# coding: utf-8
from django.conf import settings
from django.core.files.uploadedfile import (
    TemporaryUploadedFile
)
from io import BytesIO
from django.core.files.uploadhandler import FileUploadHandler, StopFutureHandlers
from rest_framework.exceptions import ParseError


class MyTemporaryFileUploadHandler(FileUploadHandler):
    """
    自定义上传处理程序，将数据流到一个临时文件。
    """
    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        """
        重写改方法，判断文件大于默认的10M不允许上传
        """
        max_size = getattr(settings, "FILE_UPLOAD_MAX_SIZE", 10485760)
        self.activated = content_length > max_size

    def new_file(self, *args, **kwargs):
        """
        Create the file object to append to as data is coming in.
        """
        super().new_file(*args, **kwargs)
        if self.activated:
            self.file = BytesIO()
            raise ParseError('文件大于最大上传限制 %s' % getattr(settings, "FILE_UPLOAD_MAX_SIZE", 10485760))
        self.file = TemporaryUploadedFile(self.file_name, self.content_type, 0, self.charset, self.content_type_extra)

    def receive_data_chunk(self, raw_data, start):
        self.file.write(raw_data)

    def file_complete(self, file_size):
        self.file.seek(0)
        self.file.size = file_size
        return self.file
