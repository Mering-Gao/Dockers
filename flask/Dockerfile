FROM  python:3.8.2

RUN pip install requests django djangorestframework django-cors-headers django-crontab haystack django-redis selenium pytest  mysqlclient  itsdangerous celery pillow QQLoginTool alipay flask==1.1.2 flask-restful flask-sqlalchemy flask-migrate flask-cors mysqlclient pymysql ipython redis qiniu pyjwt redis-py-cluster pybloomfiltermmap3 flask-limiter  -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com

WORKDIR /projects
COPY main.py /projects/main.py

EXPOSE 8000

CMD python main.py
