
import sys

sys.path.insert(0, '../../../')

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meiduo_mall.settings.dev')

from django.test import TestCase
from itsdangerous import TimedJSONWebSignatureSerializer
from django.conf import settings

# Create your tests here.
if __name__ == '__main__':
    # data + 盐  =====  itsdangerous  ===>  加密的字符串

    # obj = TimedJSONWebSignatureSerializer(秘钥, 有效期)
    obj = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=600)

    dict = {
        'name':'zs',
        'age':12
    }

    # 加密的方法dumps
    access_token = obj.dumps(dict)  # bytes(二进制)

    # 把二进制类型转为str:
    access_token = access_token.decode()

    print(access_token)

    # 解密: loads()
    data = obj.loads(access_token)

    print(data)