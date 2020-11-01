from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.views import View
from django.http import JsonResponse
from django_redis import get_redis_connection
from goods.models import SKU
from meiduo_mall.utils.views import LoginRequiredMixin
from orders.models import OrderInfo, OrderGoods
from users.models import Address
import json

class OrderSettlementView(LoginRequiredMixin, View):

    def get(self, request):
        '''呈现订单结算页面所需要的数据'''

        # 1.从mysql中获取address数据: addresses
        try:
            addresses = Address.objects.filter(user=request.user,
                                   is_deleted=False)
        except Exception as e:

            addresses = None

        address_list = []

        # 2.遍历addresses, 获取每一个address ===> {} ===> []
        for address in addresses:
            address_list.append({
              "id":address.id,
              "province":address.province.name,
              "city":address.city.name,
              "district":address.district.name,
              "place":address.place,
              "mobile":address.mobile,
              "receiver":address.receiver,
            })

        # 3.链接redis, 获取redis的链接对象
        redis_conn = get_redis_connection('carts')
        user_id = request.user.id

        # 4.从redis的hash中获取count  ====> dict
        item_dict = redis_conn.hgetall('carts_%s' % user_id )

        # 5.从redis的set中获取sku_id  ====> dict
        selected_item = redis_conn.smembers('selected_%s' % user_id)

        dict = {}

        for sku_id in selected_item:
            dict[int(sku_id)] = int(item_dict.get(sku_id))

        # 6.获取dict的所有sku_ids ===> skus
        sku_ids = dict.keys()
        try:
            skus = SKU.objects.filter(id__in=sku_ids)
        except Exception as e:
            return JsonResponse({'code':400,
                                 'errmsg':"获取不到对应的商品"})

        sku_list = []
        # 7.遍历skus, 获取每一个sku  ===> {} ====> []
        for sku in skus:
            sku_list.append({
                "id": sku.id,
                "name": sku.name,
                "default_image_url": sku.default_image_url,
                "count": dict.get(sku.id),
                "price": sku.price,
            })

        # 8.拼接参数context
        context = {
            'addresses':address_list,
            'skus':sku_list,
            'freight':10
        }
        # 9.返回json
        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'context':context})



class OrderCommitView(View):

    def post(self, request):
        '''接收参数, 保存订单信息'''

        # 1.接收json参数(address_id, pay_method)
        dict = json.loads(request.body.decode())
        address_id = dict.get('address_id')
        pay_method = dict.get('pay_method')

        # 2.总体检验
        if not all([address_id, pay_method]):
            return JsonResponse({'code':400,
                                 'errmsg':"缺少必传参数"})

        # 3.address_id检验
        try:
            address = Address.objects.get(id=address_id)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': "address_id有误"})

        # 4.pay_method检验
        # if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'],
        #                       OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
        if pay_method not in [1, 2]:
            return JsonResponse({'code': 400,
                                 'errmsg': "pay_method有误"})

        # 创建订单id:
        order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + ('%09d' % request.user.id)

        with transaction.atomic():

            save_id = transaction.savepoint()

            # 5.往订单基本信息表中保存数据
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=request.user,
                address=address,
                total_count=0,
                total_amount=Decimal('0.00'),
                freight=Decimal('10.00'),
                pay_method=pay_method,
                status=1 if pay_method == 2 else 2
            )
            # 6.链接redis, 获取redis的链接对象
            redis_conn = get_redis_connection('carts')

            # 7.从hash中获取count数据 ===> {value}
            item_dict = redis_conn.hgetall('carts_%s' % request.user.id)

            # 8.从set中获取所有的sku_ids ===> {key}
            selected_item = redis_conn.smembers('selected_%s' % request.user.id)

            dict = {}

            for sku_id in selected_item:
                dict[int(sku_id)] = int(item_dict[sku_id])


            # 9.获取{}中所有的sku_ids, 遍历, 获取每一个sku_id
            for sku_id in dict.keys():

                while True:

                    # 10.从SKU表中获取sku_id对应的sku
                    sku = SKU.objects.get(id=sku_id)

                    sales_count = dict.get(sku.id)

                    # 增加:
                    # 记录原始库存&销量
                    origin_stock = sku.stock
                    origin_sales = sku.sales

                    # 11.判断该sku的库存和销量的关系(如果库存<销量, 返回)
                    if sales_count > sku.stock:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'code':400,
                                             'errmsg':'库存不足'})

                    # 12.更改sku的stock&sales, 保存
                    # sku.stock -= sales_count
                    # sku.sales += sales_count
                    # sku.save()

                    new_stock = origin_stock - sales_count
                    new_sales = origin_sales + sales_count

                    result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,
                                                                             sales=new_sales)

                    if result == 0:
                        continue

                    # 13.更改sku对应的类别的sales, 保存
                    sku.goods.sales += sales_count
                    sku.goods.save()

                    # 14.给订单商品表增加数据
                    OrderGoods.objects.create(
                        order=order,
                        sku=sku,
                        count=sales_count,
                        price=sku.price
                    )
                    # 15.更新OrderInfo的数据
                    order.total_count += sales_count
                    order.total_amount += (sku.price * sales_count)

                    break

        order.total_amount += order.freight
        order.save()

        # 16.删除redis中set表对应的sku_id, hash也删掉
        redis_conn.hdel('carts_%s' % request.user.id, *selected_item)
        redis_conn.srem('selected_%s' % request.user.id, *selected_item)

        # 17.返回json响应
        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'order_id':order_id})














