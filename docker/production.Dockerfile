FROM python:3.8.10


#RUN  apt-get install  default-libmysqlclient-dev -y

ADD requirements.txt .
ADD docker/ansible.cfg   /etc/ansible/ansible.cfg

RUN   set -eux; apt-get update;  apt-get install -y --no-install-recommends   sshpass;  rm -rf /var/lib/apt/lists/* && \
        pip install --upgrade pip  && \
        pip install -Ur requirements.txt \
        -i https://pypi.tuna.tsinghua.edu.cn/simple  \
        --trusted-host pypi.tuna.tsinghua.edu.cn \
        --no-cache-dir && \
        pip install gunicorn[gevent] && \
        pip cache purge


WORKDIR /app

CMD ["sleep 100000"]
