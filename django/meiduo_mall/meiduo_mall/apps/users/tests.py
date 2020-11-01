# 导入 TestCase
# 自定义类继承自 TestCase
#   编写测试方法: test_ 开头
#   setUp方法: 每一个测试方法执行之前被调用
#   tearDown 方法: 每一个测试方法执行之后被调用

import json
from unittest.mock import Mock, patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase
from requests import Session
import requests
from django.test.client import Client, RequestFactory

from users.models import User
from users.views import LoginView
from users import address, user


class UserTestCase(TestCase):
    def setUp(self):
        print('setUp 每一个测试方法执行之前被调用')

    def tearDown(self):
        print('tearDown 每一个测试方法执行之后被调用')

    def test_login(self):
        print('test login')

    def test_info(self):
        print('test info')


# 自定义类继承自 TestCase
# 定义测试方法: 更新用户信息,查询用户
# 定义 setUp 创建测试用户
# 定义 tearDown 删除测试用户

class UserUpdateGetTestCase(TestCase):
    def setUp(self):
        # 创建测试用户
        # 准备用户信息
        # username
        # password
        # mobile
        # User.objects.create_user(username=username,password=password,mobile=mobile)
        self.username = 'admin'
        self.password = 'admin1234'
        self.mobile = '13812345678'
        self.user = User.objects.create_user(username=self.username, password=self.password, mobile=self.mobile)

    def tearDown(self):
        # 删除测试用户
        self.user.delete()

    def test_update(self):
        # 更新用户的 mobile
        # 准备新的手机号码
        # self.user.mobile=xxx
        # self.user.save()
        new_mobile = '13912345678'
        self.user.mobile = new_mobile
        self.user.save()

        # 验证是否更新成功
        # 读取数据库,验证手机号是否更新
        user = User.objects.get(username=self.username)
        if user.mobile == new_mobile:
            print('更新成功')
        else:
            print('更新失败')

    def test_info(self):
        user = User.objects.get(username=self.username)
        if user:
            print('获取用户信息成功')
        else:
            print('获取用户信息失败')


# setUpClass 和 tearDownClass,是类方法 @classmethod 装饰

class UpDownClassTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        print('Up class 整个类只执行一次,所有测试方法之前')

    @classmethod
    def tearDownClass(cls):
        print('Down class 整个类只执行一次,所有测试方法之后')

    def setUp(self):
        print('setUp 整个类只执行一次,每个测试方法之前')

    def tearDown(self):
        print('tearDown 整个类只执行一次,每个测试方法之后')

    def test_1(self):
        print('test 1')

    def test_2(self):
        print('test 2')


# 测试获取用户信息接口和获取用户浏览历史接口
# 测试之前需要先登录
# 代码逻辑
# 登录在 setUpClass
# 退出在 tearDownClass
# 获取用户信息 test_get_info 方法
# 获取浏览历史 test_history 方法

class UserInfoHistory(TestCase):

    @classmethod
    def setUpClass(cls):
        # 实现状态保持 self.session.[post|get]
        # 准备数据 auth ={}
        # session.post(url,json)
        # 判断登录是否成功
        cls.session = Session()
        auth = {
            'username': 'root',
            'password': 'root1234'
        }
        url = 'http://localhost:8000/login/'
        resp = cls.session.post(url, json=auth)
        print(resp.content)
        dict_data = resp.json()
        if dict_data['code'] != 0:
            print('登录失败')

    @classmethod
    def tearDownClass(cls):
        # 退出登录
        url = 'http://localhost:8000/logout/'
        cls.session.delete(url)

    def test_get_info(self):
        # 调用用户信息接口
        # 判断用户信息是否获取成功
        url = 'http://localhost:8000/info/'
        resp = self.session.get(url)
        dict_data = resp.json()
        if dict_data['code'] != 0:
            print('获取用户信息失败')
        else:
            print(dict_data)

    def test_history(self):
        # 调用用户浏览历史接口
        # 判断浏览历史是否获取成功
        url = 'http://localhost:8000/browse_histories/'
        resp = self.session.get(url)
        dict_data = resp.json()
        if dict_data['code'] != 0:
            print('浏览历史获取失败')
        else:
            print(dict_data)


# django 通过判断测试方法抛出异常,来把方法标记为测试不通过

class DjangoTestCase(TestCase):

    def test_trint_error(self):
        print('test_trint_error')
        url = 'http://localhost:8000/info/'
        resp = requests.get(url)
        dict_data = resp.json()
        if dict_data['code'] != 0:
            print(f'获取用户信息失败:{dict_data["errmsg"]}')

    def test_raise_error(self):
        print('test_raise_error')
        url = 'http://localhost:8000/info/'
        resp = requests.get(url)
        dict_data = resp.json()
        # 手动抛出异常
        # if dict_data['code'] != 0:
        # raise AssertionError(f'获取用户信息失败:{dict_data["errmsg"]}')

        self.assertEqual(dict_data['code'], 0, msg=f'获取用户信息失败:{dict_data["errmsg"]}')


# 通过 client 进行登录
# setUp 创建临时用户
# tearDown 删除临时用户
# 测试方法中 client.login(username=xxx,password=yyyy)

class ClientLoginTestCase(TestCase):
    def setUp(self):
        # 创建临时用户
        # 准备数据
        # username
        # password
        # mobile
        # User.objects.create_user
        self.username = 'zhangsan'
        self.password = 'zhangsan1234'
        self.mobile = '13812345678'
        self.user = User.objects.create_user(username=self.username, password=self.password, mobile=self.mobile)

    def tearDown(self):
        # 删除临时用户
        self.user.delete()

    def test_login(self):
        # 实例化 client
        # client.login(username=xxx,password=yyy) 返回 bool 值,True 表示成功
        # 断言
        client = Client()
        is_login = client.login(username=self.username, password=self.password)

        # self.assertEqual(is_login,True,)
        self.assertTrue(is_login, msg='登录失败')


# 通过 client.get 测试用户信息接口
# setUp 创建临时用户
# tearDown 删除临时用户
# 测试方法中
# 1. client.login(username=xxx,password=yyyy)
# 2. client.get(path)
# 3. 断言


class UserInfoTestCase(TestCase):
    def setUp(self):
        # 创建临时用户
        # 准备数据
        # username
        # password
        # mobile
        # User.objects.create_user
        self.username = 'zhangsan'
        self.password = 'zhangsan1234'
        self.mobile = '13812345678'
        self.user = User.objects.create_user(username=self.username, password=self.password, mobile=self.mobile)

    def tearDown(self):
        # 删除临时用户
        self.user.delete()

    def test_info(self):
        # 登录
        # 获取用户信息
        client = Client()
        is_login = client.login(username=self.username, password=self.password)
        self.assertTrue(is_login, msg='登录失败')

        path = '/info/'

        resp = client.get(path)

        dict_data = resp.json()

        self.assertEqual(dict_data['code'], 0, msg='获取用户信息失败')


# 通过 client.post 测试用户登录
# setUp 创建临时用户
# tearDown 删除临时用户
# 测试方法中
# 1. resp = client.post(path,data,content_type="application/json")
# 2. 断言
# 3. client.get('/info/')

class UserLoginTestCase(TestCase):
    def setUp(self):
        # 创建临时用户
        # 准备数据
        # username
        # password
        # mobile
        # User.objects.create_user
        self.username = 'zhangsan'
        self.password = 'zhangsan1234'
        self.mobile = '13812345678'
        self.user = User.objects.create_user(username=self.username, password=self.password, mobile=self.mobile)

    def tearDown(self):
        # 删除临时用户
        self.user.delete()

    def test_login(self):
        # 实例化 client
        # client.post
        # path = '/login/'

        client = Client()
        path = '/login/'
        auth = {
            'username': self.username,
            'password': self.password
        }
        resp = client.post(path, data=auth, content_type='application/json')
        dict_data = resp.json()
        self.assertEqual(dict_data['code'], 0, msg='登录失败')

        # 获取用户信息
        resp = client.get('/info/')
        print(resp.json())


# 1. 创建测试用户
# 2. 构造请求对象 request
# 3. 可选的调用中间进行处理
# 4. 实例化 login_view= LoginView()
# 5. 调用 post 方法 resp = login_view.post(request)
# 6. 可选的调用中间进行处理


class FactoryTestCase(TestCase):
    def setUp(self) -> None:
        self.username = 'zhangsan'
        self.password = 'zhangsan1234'
        self.mobile = '13812345678'
        self.user = User.objects.create_user(username=self.username, password=self.password, mobile=self.mobile)

    def tearDown(self) -> None:
        # 删除临时用户
        self.user.delete()

    def test_post(self):
        # 实力化 factory = RequestFactory()
        # request = factory.post(path,data={},content_type='xxx')
        # 中间件调用
        # 实例化 login_view= LoginView()
        # 调用 post 方法 resp = login_view.post(request)
        # 断言

        factory = RequestFactory()
        path = '/login/'
        auth = {
            'username': self.username,
            'password': self.password
        }
        request = factory.post(path, data=auth, content_type='application/json')

        # 中间件调用
        # 实例化中间件对象 middleware = SessionMiddleware()
        # middleware.process_request(request)
        middleware = SessionMiddleware()
        middleware.process_request(request)

        login_view = LoginView()
        resp = login_view.post(request)
        content = resp.content
        dict_data = json.loads(content)
        print(dict_data)

        self.assertEqual(dict_data['code'], 0, msg='登录失败')


# 测试 mock 对象
# mock --> return_value
# mock --> side_effect=[异常对象,可迭代,函数]


class MockTestCase(TestCase):

    def test_return_value(self):
        # 实例化 mock 对象 mock=Mock(return_value)
        # mock() 返回 return_value
        mock = Mock(return_value=12345)
        result = mock()
        print(result)  # 12345

    def test_side_effect_exception(self):
        # 实例化 mock 对象 mock=Mock(side_effect=异常对象)
        # mock() 抛出异常对象
        mock = Mock(side_effect=AssertionError('test'))
        mock()  # 抛出异常对象

    def test_side_effect_iter(self):
        # 实例化 mock 对象 mock=Mock(side_effect=可迭代对象)
        # mock() 遍历可迭代对象
        mock = Mock(side_effect=[1, 2, 3])
        print(mock())  # 1
        print(mock())  # 2
        print(mock())  # 3
        print(mock())  # 抛出异常

    def test_side_effect_function(self):
        # 实例化 mock 对象 mock=Mock(side_effect=函数)
        # mock() 调用对应的函数
        def function(a, b):
            return a + b

        mock = Mock(side_effect=function)
        print(mock(1, 9))  # 10
        print(mock())  # 抛出异常


# 测试 users.user.user_info
# users.user.user_info 调用了 users.address.default 方法,该方法没有实现,此时用户 mock 对象替换 address.default

class UserDefaultInfoTestCase(TestCase):
    def setUp(self):
        self.username = 'zhangsan'
        self.password = 'As9034123'
        self.mobile = '13712345678'
        self.user = User.objects.create_user(username=self.username,
                                             password=self.password,
                                             mobile=self.mobile)

    def tearDown(self):
        self.user.delete()

    def test_userinfo(self):
        # 实例化 mock 对象
        # address.default =mock
        # 调用 user.user_info
        print('test_userinfo')
        mock = Mock(return_value={'title': '公司', 'mobile': '13812345678', 'place': '浦东新区航头镇108 号', 'receiver': '张三'})
        address.default = mock
        userinfo = user.user_info(self.user.id)
        print(userinfo)

    def test_userinfo_nomock(self):
        print('test_userinfo_nomock')
        userinfo = user.user_info(self.user.id)
        print(userinfo)


# 限制 mock 的范围
# @path('对象的完整路径')
# def test_xxx(self,mock_obj):
#    mock_obj.return_value =xxxx

# with path('对象的完整路径') as mock_obj:
#     mock_obj.return_value =xxxx


class PatchTestCase(TestCase):
    def setUp(self):
        self.username = 'zhangsan'
        self.password = 'As9034123'
        self.mobile = '13712345678'
        self.user = User.objects.create_user(username=self.username,
                                             password=self.password,
                                             mobile=self.mobile)

    def tearDown(self):
        self.user.delete()

    # @patch('users.address.default')
    @patch('users.address.default')
    def test_userinfo_1(self, mock_obj):
        mock_obj.return_value = {'title': '公司', 'mobile': '13812345678', 'place': '浦东新区航头镇108 号', 'receiver': '张三'}
        userinfo = user.user_info(self.user.id)
        print(userinfo)

    def test_userinfo_2(self):
        with patch('users.address.default') as mock_obj:
            # mock 有效范围
            mock_obj.return_value = {'title': '公司', 'mobile': '13812345678', 'place': '徐家汇区 188 号', 'receiver': '李四'}
            userinfo = user.user_info(self.user.id)
            print(userinfo)
        # mock 无效范围
        userinfo = user.user_info(self.user.id)
        print(userinfo)


class MockPropertyMethodTestCase(TestCase):

    def test_mock(self):
        # called
        # 是否被调用过, 返回布尔值
        # call_count
        # 获取调用测试, 返回调用测试
        # call_args
        # 最后一次调用时使用的参数, 未调用返回None
        # call_args_list 所有调用时使用的参数列表
        mock = Mock(return_value=123)
        print(mock.called)  # Flase
        mock()
        print(mock.called)  # True
        print(mock.call_count)  # 1

        mock(1, 2)
        print(mock.call_args)  # 1,2

        print(mock.call_args_list)  # [None,(1,2)]

        # assert_called
        # 检查是否被调用过，如果没有被调用过，则会抛出 AssertionError异常
        # assert_called_once()
        # 确保调用过一次，如果没调用或多于一次，则抛出AssertionError异常
        # assert_not_called
        # 确保没被调用过，否则抛出 \ AssertionError\ 异常
        # assert_called_with(*args, **kargs) 检查最后一次调用时使用的参数

        print('assert_called')
        mock.assert_called()  # 注意是否可以调用
        try:
            print('assert_called_once')
            mock.assert_called_once()  # 断言失败
        except Exception:
            print('assert_called_once 失败')

        print('assert_not_called')
        mock.assert_not_called()  # 断言失败

        print('assert_called_with')
        mock.assert_called_with(1, 2)  # 断言成功
