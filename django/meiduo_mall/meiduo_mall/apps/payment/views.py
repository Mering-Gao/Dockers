from django.http import JsonResponse
from django.views import View
from orders.models import OrderInfo
from django.conf import settings
import os

from payment.models import Payment


class PaymentsView(View):

    def get(self, request, order_id):
        '''支付的第一个接口'''

        # 1.根据order_id获取订单
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=request.user,
                                          status=1)
        except Exception as e:
            return JsonResponse({'code':400,
                                 'errmsg':'order_id有误'})

        # 2.调用python-alipay-sdk的类: Alipay
        # 3.利用这个类, 生成对象 alipay
        from alipay import AliPay

        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )


        # 4.调用该对象的方法
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="美多商城%s" % order_id,
            return_url=settings.ALIPAY_RETURN_URL,
        )

        # 5.拼接url
        url = settings.ALIPAY_URL + '?' + order_string

        # 6.返回json
        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'alipay_url':url})

class SavePaymentView(View):
    
    def put(self, request):
        '''保存支付结果'''
        
        # 1.接收参数(查询字符串)
        query_dict = request.GET
        dict = query_dict.dict()

        # 2.把查询字符串参数中的sign(k&v)剔除. 获取剔除的结果
        signature = dict.pop('sign')
        from alipay import AliPay

        # 3.获取python-alipay-sdk的类, 用该类创建对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )

        # 4.调用对象的验证函数verify
        isSuccess = alipay.verify(dict, signature)

        # 5.判断验证的结果, 如果为True
        if isSuccess:
            # 6.从dict中获取order_id, 流水号
            order_id = dict.get('out_trade_no')
            trade_id = dict.get('trade_no')

            # 7.保存order_id, 流水号到支付表中
            try:
                Payment.objects.create(
                    order_id = order_id,
                    trade_id = trade_id
                )

                # 8.更改订单的状态: 从未支付 ===> 未评论
                OrderInfo.objects.filter(order_id=order_id,
                                         status=1).update(status=4)

            except Exception as e:
                return JsonResponse({'code': 400,
                                     'errmsg': '保存失败'})

            # 9.拼接参数, 返回
            return JsonResponse({'code':0,
                                 'errmsg':'ok',
                                 'trade_id':trade_id})
        else:
            # 10.如果结果为False, 警告
            return JsonResponse({'code':400,
                                 'errmsg':'非法请求'})




























