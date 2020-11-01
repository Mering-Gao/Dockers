# 1. 调用获取图形验证码接口 这里需要生成一个 uuid 作为路径参数，并且后续作为 image_code_id

# 2. 读取 redis 中生层的验证码
# 获取 redis 的连接 redis_conn = get_redis_connection('verify_code')
# 读取验证码 imagecode = redis_conn.get(f'img{image_code_id}').decode()

# 3. mock 掉短信发送模块

# 4. 构建请求数据
# mobile = '13612345678' 手机号码
# path = f'/sms_codes/{mobile}/' 访问路径
# image_code_id  第 1 步中的 image_code_id
# image_code  第 2 步中 image_code

# 5. 发送请求 通过 client 对象发起请求

# 6. 验证结果
# 检查接口返回的 code
# 验证 redis 中是否写入了手机验证码
# 验证 reids 中是否写入了已发送手机验证码
# 验证发送手机短信的方法是否被调用

# 7. 清理调用测试过程中产生的临时数据 redis_conn.delete(f'sms_{mobile}', f'flag_{mobile}', f'img_{image_code_id}'

import uuid
from unittest.mock import patch

from django.test import TestCase, Client
from django_redis import get_redis_connection


class SMSCodeTestCase(TestCase):

    def setUp(self) -> None:
        # image_code_id
        self.image_code_id = str(uuid.uuid4())
        # image_code
        # 请求获取图片验证码接口
        # 读取 redis 数据
        path = f'/image_codes/{self.image_code_id}/'
        self.client = Client()
        resp = self.client.get(path)
        print(resp.status_code)

        redis_conn = get_redis_connection('verify_code')
        self.image_code = redis_conn.get(f'img_{self.image_code_id}').decode()

        # mobile
        self.mobile = '13123456789'

    def tearDown(self) -> None:
        redis_conn = get_redis_connection('verify_code')
        redis_conn.delete(f'sms_{self.mobile}', f'flag_{self.mobile}', f'img_{self.image_code_id}')

    @patch('meiduo_mall.libs.yuntongxun.ccp_sms.CCP.send_template_sms')
    def test_send_code(self, mock_obj):
        # 请求获取手机验证码接口
        path = f'/sms_codes/{self.mobile}/'
        data = {
            'image_code_id': self.image_code_id,
            'image_code': self.image_code
        }

        resp = self.client.get(path, data=data)

        print(resp.content)

        dict_data = resp.json()

        # 验证
        # 检查接口返回的 code
        self.assertEqual(dict_data['code'], 0, msg='短信发送失败')
        # 验证 redis 中是否写入了手机验证码
        redis_conn = get_redis_connection('verify_code')
        sms_code = redis_conn.get(f'sms_{self.mobile}')
        self.assertIsNotNone(sms_code, msg='redis 中没有写入手机验证码')
        # 验证 reids 中是否写入了已发送手机验证码
        sms_flag = redis_conn.get(f'flag_{self.mobile}')
        self.assertIsNotNone(sms_code, msg='redis 中没有写入已经发送验证码')
        # 验证发送手机短信的方法是否被调用
        mock_obj.assert_called()
