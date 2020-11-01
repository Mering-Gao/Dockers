from QQLoginTool.QQtool import OAuthQQ
from django.contrib.auth import login
from django.shortcuts import render
from django.views import View
from django.conf import settings
from django.http import JsonResponse
import logging
import json, re

from carts.utils import merge_cookie_to_redis
from oauth.models import OAuthQQUser
from oauth.utils import generate_access_token_by_openid, check_access_token
from django_redis import get_redis_connection

from users.models import User

logger = logging.getLogger('django')


class QQURLView(View):
    
    def get(self, request):
        '''QQ登录的第一个接口, 返回qq的网址'''
        
        # 1.接收查询字符串参数
        next = request.GET.get('next')

        # 2.用QQLoginTool工具类创建对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)

        # 3.利用对象, 调用函数, 获取qq登录的地址
        url = oauth.get_qq_url()

        # 4.返回json(code, errmsg, login_url)
        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'login_url':url})


class QQURLSecondView(View):

    def get(self, request):
        '''qq登录的第二个接口'''

        # 1.接收参数(查询字符串类型)
        code = request.GET.get('code')

        # 2.判断参数是否存在
        if not code:
            return JsonResponse({'code':400,
                                 'errmsg':"code不存在"})

        # 3.获取QQLoginTool工具类的对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)

        try:
            # 4.调用对象的方法, 获取access_token
            access_token = oauth.get_access_token(code)

            # 5.调用对象的方法, 根据access_token获取openid
            openid = oauth.get_open_id(access_token)

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code':400,
                                 'errmsg':"获取openid出错"})


        try:
            # 6.根据openid这个条件, 去到QQ表中获取对应的对象
            oauth_qq = OAuthQQUser.objects.get(openid=openid)
        except Exception as e:
            # 11.如果该对象获取不到, 说明qq表中不存在该记录
            # 12.封装一个函数: 把openid加密为access_token
            access_token = generate_access_token_by_openid(openid)

            # 13.把access_token返回给前端
            # 返回的code不要为:0,因为前端设置了: 返回0进入首页.
            return JsonResponse({'code':300,
                                 'errmsg':'ok',
                                 'access_token':access_token})
        else:
            # 7.如果该对象获取到了. 算是登录成功
            user = oauth_qq.user

            # 8.实现状态保持
            login(request, user)


            response = JsonResponse({'code':0,
                                     'errmsg':'ok'})

            # 9.设置cookie(username)
            response.set_cookie('username', user.username, max_age=3600 * 24 * 14)

            # 10.返回响应
            # 增加合并购物车功能:
            response = merge_cookie_to_redis(request, response)

            # 12.返回结果(json)
            return response



    def post(self, request):
        '''qq登录的第三个接口'''

        # 1.接收参数(json)
        dict = json.loads(request.body.decode())
        mobile = dict.get('mobile')
        password = dict.get('password')
        sms_code_client = dict.get('sms_code')
        access_token = dict.get('access_token')

        # 2.总体检验,查看是否为空
        if not all([mobile, password, sms_code_client, access_token]):
            return JsonResponse({'code':400,
                                 'errmsg':'缺少必传参数'})

        # 3.mobile单个检验
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': 'mobile格式有误'})

        # 4.password单个检验
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return JsonResponse({'code': 400,
                                 'errmsg': 'password格式有误'})


        # 5.链接redis, 获取redis的链接对象
        redis_conn = get_redis_connection('verify_code')

        # 6.从redis中获取服务端的短信验证码
        sms_code_server = redis_conn.get('sms_%s' % mobile)

        # 7.判断服务端的短信验证码是否过期
        if not sms_code_server:
            return JsonResponse({'code': 400,
                                 'errmsg': '短信验证码过期'})

        # 8.对比前后端的短信验证码
        if sms_code_client != sms_code_server.decode():
            return JsonResponse({'code': 400,
                                 'errmsg': '输入的短信验证码有误'})

        # 9.自定义一个函数,把access_token解密:openid
        openid = check_access_token(access_token)

        # 10.判断openid是否存在,如果存在没问题
        if openid is None:
            return JsonResponse({'code': 400,
                                 'errmsg': 'openid为空'})

        try:
            # 11.从User表中获取一个该手机号对应的用户
            user = User.objects.get(mobile=mobile)
        except Exception as e:
            # 12.如果该用户不存在, 给User增加一个新的记录
            user = User.objects.create_user(username=mobile,
                                            password=password,
                                            mobile=mobile)
        else:
            # 13.如果该用户存在, 比较密码是否一致
            if not user.check_password(password):
                return JsonResponse({'code': 400,
                                 'errmsg': '密码输入的不对'})


        # 14.把openid和user保存到QQ表中
        try:
            OAuthQQUser.objects.create(openid=openid,
                                       user=user)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': '保存到qq表中出错'})

        # 15.状态保持
        login(request, user)


        response = JsonResponse({'code':0,
                                 'errmsg':'ok'})

        # 16.设置cookie:username
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)

        # 17.返回json
        # 增加合并购物车功能:
        response = merge_cookie_to_redis(request, response)


        # 12.返回结果(json)
        return response


















