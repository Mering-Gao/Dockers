
from meiduo_mall.libs.yuntongxun.ccp_sms import CCP
from django.contrib.auth import authenticate
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from django.http import HttpResponse
from meiduo_mall.libs.captcha.captcha import captcha
from django.http import JsonResponse
import logging
import random

logger = logging.getLogger('django')


class ImageCodeView(View):

    def get(self, request, uuid):
        '''生成图形验证码,保存后返回'''
        # 1.调用captcha框架,生成图片和对应的信息
        text, image = captcha.generate_captcha()

        # 2.链接redis, 获取redis的链接对象
        redis_conn = get_redis_connection('verify_code')

        # 3.调用链接对象, 把数据保存到redis
        redis_conn.setex('img_%s' % uuid, 300, text)

        # 4.返回图片给前端
       # return HttpResponse(image,
       #                     content_type = 'image/jpg')

        # 判断是否是 debug 状态
        # 如果是 debug 状态就把 text 返回给前端
        # 如果不是，就单独把图片返回给客户端

        from django.conf import settings
        print(settings.DEBUG)
        if settings.DEBUG:
            response = HttpResponse(image,
                                    content_type='image/jpeg')

            response.set_cookie('image_code', text)
            return response
        else:
            return HttpResponse(image,
                                content_type='image/jpeg')


class SMSCodeView(View):

    def get(self, request, mobile):
        '''接收参数, 检验, 发送短信验证码'''

        # 额外增加的功能: 避免频繁发送短信验证码
        # 0. 从redis中获取60s保存的信息
        redis_conn = get_redis_connection('verify_code')

        flag = redis_conn.get('flag_%s' % mobile)

        # 0.1 判断该值是否存在, 如果不存在, 进行下面的步骤, 如果存在, 返回
        if flag:
            return JsonResponse({'code': 400,
                                 'errmsg': "请不要频繁发送短信验证码"})

        # 1.接收查询字符串参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # 2.总体检验(查看参数是否为空)
        if not all([image_code_client, uuid]):
            return JsonResponse({'code': 400,
                                 'errmsg': "必传参数不能为空"})

        # 3.链接redis, 获取redis的链接对象
        # 这里的步骤挪到了上面

        # 4.从redis中取出图形验证码
        image_code_server = redis_conn.get('img_%s' % uuid)

        # 5.判断服务端的图形验证码是否过期, 如果过期, return
        if image_code_server is None:
            return JsonResponse({'code': 400,
                                 'errmsg': "图形验证码过期"})

        # 6.删除redis中图形验证码
        try:
            redis_conn.delete('img_%s' % uuid)
        except Exception as e:
            logger.info(e)

        # 7.对比前后端的图形验证码
        if image_code_client.lower() != image_code_server.decode().lower():
            return JsonResponse({'code': 400,
                                 'errmsg': "输入的图形验证码出错"})

        # 8.随机生成6为的短信验证码
        sms_code = '%06d' % random.randint(0, 999999)

        # 9.打印短信验证码
        logger.info(sms_code)

        # 创建redis管道:
        pl = redis_conn.pipeline()

        # 10.把短信验证码保存到redis
        pl.setex('sms_%s' % mobile, 300, sms_code)

        pl.setex('flag_%s' % mobile, 60, 1)

        # 执行管道:
        pl.execute()

        # 11.调用容联云, 发送短信验证码
        CCP().send_template_sms(mobile, [sms_code, 5], 1)
        # 添加一个提示celery抛出任务的提醒:
        from django.conf import settings
        if settings.DEBUG:
            return JsonResponse({
                'code': 0,
                'errmsg': 'ok',
                'sms_code': sms_code
            })
        # 12.返回json
        return JsonResponse({'code': 0,
                             'errmsg': "ok"})
