import base64
import pickle

from django.shortcuts import render
from django.views import View
import json
from django.http import JsonResponse
from django_redis import get_redis_connection
# Create your views here.
from goods.models import SKU


class CartsView(View):

    def post(self, request):
        '''接收购物车参数,保存'''

        # 1.接收json参数
        dict = json.loads(request.body.decode())
        sku_id = dict.get('sku_id')
        count = dict.get('count')
        selected = dict.get('selected', True)

        # 2.总体检验是否为空
        if not all([sku_id, count]):
            return JsonResponse({'code':400,
                                'errmsg':'必传参数为空'})

        # 3.单个检验sku_id是否存在
        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': 'sku_id参数有误'})

        # 4.count是否是个数字
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': 'count参数有误'})

        # 5.判断selected是否存在,如果存在,是不是bool值
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code': 400,
                                     'errmsg': 'selected参数有误'})

        # 6.判断用户是否登录,
        if request.user.is_authenticated:
            # 8.如果用户登录, 进入这里
            # 9.链接redis, 获取链接对象
            redis_conn = get_redis_connection('carts')

            # 10.往redis的hash中增加数据: carts_user_id : {sku_id : count}
            redis_conn.hincrby('carts_%s' % request.user.id,
                               sku_id,
                               count)

            # 11.往redis的set中增加数据: selected_user_id:{sku_id1, sku_id2, ...}
            redis_conn.sadd('selected_%s' % request.user.id,
                            sku_id)

            # 12.返回json结果
            return JsonResponse({'code': 0,
                                 'errmsg': 'ok'})

        else:
            # 7.如果没有登录, 进入这里
            # 13.从cookie中获取对应的数据
            cart_cookie = request.COOKIES.get('carts')

            # 14.判断该数据是否存在, 如果存在, 解密 ===> dict
            if cart_cookie:
                cart_dict = pickle.loads(base64.b64decode(cart_cookie))
            else:
                # 15.如果不存在, 创建一个新的dict
                cart_dict = {}

            # 16.判断sku_id是否存在于dict中
            if sku_id in cart_dict:
                # 17.如果在, count要进行累加
                count += cart_dict[sku_id]['count']

            # 18.更新字典
            cart_dict[sku_id] = {
                'count':count,
                'selected':selected
            }
            # 19.把dict加密, 得到加密的结果
            cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()

            response = JsonResponse({'code':0,
                                     'errmsg':'Ok'})

            # 20.把加密的结果, 写入到cookie
            response.set_cookie('carts', cart_data, max_age=3600 * 24 * 14)

            # 21.返回响应(cookie)
            return response

    def get(self, request):
        '''获取购物车数据'''

        # 1.判断用户是否登录
        if request.user.is_authenticated:
            # 2.如果用户登录
            # 3.链接redis, 获取链接对象
            redis_conn = get_redis_connection('carts')

            # 4.从hash中获取对应的数据: dict
            item_dict  =redis_conn.hgetall('carts_%s' % request.user.id)

            # 5.从set中获取对应的数据: 集合{}
            selected_items = redis_conn.smembers('selected_%s' % request.user.id)

            cart_dict = {}

            # 6.把hash中的sku_id & count 放到 {} 中
            # 7.判断hash中的sku_id 是否在 set 的集合中
            for sku_id, count in item_dict.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in selected_items
                }

        else:
            # 8.如果用户未登录
            # 9.从cookie中获取数据
            cookie_cart = request.COOKIES.get('carts')

            # 10.判断该数据是否存在, 如果存在, 解密 ===> dict
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart))
            else:
                # 11.如果不存在, 创建新的dict
                cart_dict = {}

        # 12.根据dict, 获取对赢的key: sku_ids
        sku_ids = cart_dict.keys()

        # 13.把sku_ids ===> skus
        try:
            skus = SKU.objects.filter(id__in=sku_ids)
        except Exception as e:
            return JsonResponse({'code':400,
                                 'errmsg':"查询数据库报错"})

        list = []

        # 14.遍历skus, 获取每一个sku ===> {} === []
        for sku in skus:
            list.append({
                'id':sku.id,
                'default_image_url':sku.default_image_url,
                'name':sku.name,
                'price':sku.price,
                'count':cart_dict.get(sku.id).get('count'),
                'amount':(sku.price * cart_dict.get(sku.id).get('count')),
                'selected':cart_dict.get(sku.id).get('selected')
            })

        # 15.拼接参数(json), 返回
        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'cart_skus':list})


    def put(self, request):
        '''修改购物车'''
        # 1.接收json参数sku_id, count & selected
        dict = json.loads(request.body.decode())
        sku_id = dict.get('sku_id')
        count = dict.get('count')
        selected = dict.get('selected', True)

        # 2.总体检验是否为空
        if not all([sku_id, count]):
            return JsonResponse({'code': 400,
                                 'errmsg': '必传参数为空'})

        # 3.单个检验sku_id是否存在
        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': 'sku_id参数有误'})

        # 4.count是否是个数字
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': 'count参数有误'})

        # 5.判断selected是否存在,如果存在,是不是bool值
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code': 400,
                                     'errmsg': 'selected参数有误'})

        # 3.判断用户是否登录
        if request.user.is_authenticated:
            # 4.如果用户登录
            # 5.链接redis, 获取链接对象
            redis_conn = get_redis_connection('carts')

            # 6.修改hash中的数据
            redis_conn.hset('carts_%s' % request.user.id,
                               sku_id,
                               count)

            # 7.判断selected是否是True
            if selected:
                # 8.如果是True, 往set中增加当前商品的id:sku_id
                redis_conn.sadd('selected_%s' % request.user.id,
                                sku_id)
            else:
                # 9.如果是False, 从set中删除当前商品的id:sku_id
                redis_conn.srem('selected_%s' % request.user.id,
                                sku_id)

            dict = {
                'id': sku_id,
                'count': count,
                'selected': selected
            }

            # 10.拼接参数, 返回json
            return JsonResponse({'code': 0,
                                 'errmsg': 'ok',
                                 'cart_sku':dict})

        else:
            # 11.如果用户未登录:
            # 12.读取cookie中的数据, 如果数据存在 ===> 解密 ===> dict
            cart_cookie = request.COOKIES.get('carts')

            if cart_cookie:
                cart_dict = pickle.loads(base64.b64decode(cart_cookie))
            else:
                # 13.如果数据不存在, 创建新的dict
                cart_dict = {}

            # 14.把前端传入的三个参数,写入dict
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 19.把dict加密, 得到加密的结果
            cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()

            dict = {
                'id': sku_id,
                'count': count,
                'selected': selected
            }

            # 10.拼接参数, 返回json
            response = JsonResponse({'code': 0,
                                     'errmsg': 'ok',
                                     'cart_sku': dict})

            # 20.把加密的结果, 写入到cookie
            response.set_cookie('carts', cart_data, max_age=3600 * 24 * 14)

            # 21.返回响应(cookie)
            return response


    def delete(self, request):
        '''删除对应的商品记录'''

        # 1.接收参数sku_id
        dict = json.loads(request.body.decode())
        sku_id = dict.get('sku_id')

        # 2.检验参数
        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': 'sku_id参数有误'})

        # 3.判断用是否登录
        if request.user.is_authenticated:
            # 4.如果用户登录,
            # 5.链接redis, 获取链接对象
            redis_conn = get_redis_connection('carts')

            # 6.删除hash中的值
            redis_conn.hdel('carts_%s' % request.user.id, sku_id)

            # 7.删除set中的值
            redis_conn.srem('selected_%s' % request.user.id,
                                sku_id)

            # 8.返回json
            return JsonResponse({'code': 0,
                                 'errmsg': 'ok'})
        else:
            # 9.如果用户未登录
            cart_cookie = request.COOKIES.get('carts')

            # 11.如果该值存在, 解密 ===> dict
            if cart_cookie:
                cart_dict = pickle.loads(base64.b64decode(cart_cookie))
            else:
                cart_dict = {}

            # 10.拼接参数, 返回json
            response = JsonResponse({'code': 0,
                                     'errmsg': 'ok'})

            # 12.判断sku_id是否在dict中
            if sku_id in cart_dict:
                # 13.如果在dict, 把dict中该sku_id对应的一条记录删掉
                del cart_dict[sku_id]

                # 14.吧dict再次进行加密, 写入到cookie中
                cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()

                # 把加密的结果, 写入到cookie
                response.set_cookie('carts', cart_data, max_age=3600 * 24 * 14)

            # 15.返回json
            return response


class SelectAllView(View):

    def put(self, request):
        '''全选或全不选接口'''

        # 1.接收json参数, selected
        dict = json.loads(request.body.decode())
        selected = dict.get('selected', True)

        # 2.检验参数是否是bool值
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code': 400,
                                     'errmsg': 'selected参数有误'})

        # 3.判断用户是否登录
        if request.user.is_authenticated:
            # 4.如果用户登录, 链接redis, 获取链接对象
            redis_conn = get_redis_connection('carts')

            # 5.把hash中的sku_ids取出
            item_dict = redis_conn.hgetall('carts_%s' % request.user.id)
            sku_ids = item_dict.keys()

            # 6.判断selected是否是 True
            if selected:
                # 7.如果是, 把sku_ids全部增加到set
                redis_conn.sadd('selected_%s' % request.user.id, *sku_ids)
            else:
                # 8.如果不是, 把sku_ids全部从set删除
                redis_conn.srem('selected_%s' % request.user.id, *sku_ids)

            # 9.返回json
            return JsonResponse({'code': 0,
                                 'errmsg': 'ok'})

        else:
            # 10.如果用户未登录
            # 11.从cookie中取值
            cart_cookie = request.COOKIES.get('carts')

            # 10.拼接参数, 返回json
            response = JsonResponse({'code': 0,
                                     'errmsg': 'ok'})

            # 12.判断该值是否存在, 如果存在
            if cart_cookie:
                cart_dict = pickle.loads(base64.b64decode(cart_cookie))

                # 13.遍历字典, 获取dict中每一个selected
                for sku_id in cart_dict.keys():
                    # 14.用前端传入的selected更新(覆盖)selected
                    cart_dict[sku_id]['selected'] = selected

                # 15.加密 , 写入cookie
                cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()

                # 20.把加密的结果, 写入到cookie
                response.set_cookie('carts', cart_data, max_age=3600 * 24 * 14)

            # 16.返回
            return response



class SimpleCartsView(View):

    def get(self, request):
        '''获取购物车数据'''

        # 1.判断用户是否登录
        if request.user.is_authenticated:
            # 2.如果用户登录
            # 3.链接redis, 获取链接对象
            redis_conn = get_redis_connection('carts')

            # 4.从hash中获取对应的数据: dict
            item_dict = redis_conn.hgetall('carts_%s' % request.user.id)

            # 5.从set中获取对应的数据: 集合{}
            selected_items = redis_conn.smembers('selected_%s' % request.user.id)

            cart_dict = {}

            # 6.把hash中的sku_id & count 放到 {} 中
            # 7.判断hash中的sku_id 是否在 set 的集合中
            for sku_id, count in item_dict.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in selected_items
                }

        else:
            # 8.如果用户未登录
            # 9.从cookie中获取数据
            cookie_cart = request.COOKIES.get('carts')

            # 10.判断该数据是否存在, 如果存在, 解密 ===> dict
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart))
            else:
                # 11.如果不存在, 创建新的dict
                cart_dict = {}

        # 12.根据dict, 获取对赢的key: sku_ids
        sku_ids = cart_dict.keys()

        # 13.把sku_ids ===> skus
        try:
            skus = SKU.objects.filter(id__in=sku_ids)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': "查询数据库报错"})

        list = []

        # 14.遍历skus, 获取每一个sku ===> {} === []
        for sku in skus:
            list.append({
                'id': sku.id,
                'default_image_url': sku.default_image_url,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
            })

        # 15.拼接参数(json), 返回
        return JsonResponse({'code': 0,
                             'errmsg': 'ok',
                             'cart_skus': list})
































