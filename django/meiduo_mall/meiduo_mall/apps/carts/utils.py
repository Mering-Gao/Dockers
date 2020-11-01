import pickle, base64
from django_redis import get_redis_connection

def merge_cookie_to_redis(request, response):
    '''合并cookie中的购物车数据到redis'''

    # 1.读取cookie中的数据
    cookie_cart = request.COOKIES.get('carts')

    # 判断该数据是否存在
    if not cookie_cart:
        return response

    # 2.如果存在,解密  ===> dict
    cart_dict = pickle.loads(base64.b64decode(cookie_cart))

    new_dict = {}  # hash
    new_add = []
    new_remove = []
    # 3.把dict的数据分为三部分 ===> dict={} add=[] remove=[]
    for sku_id, dict in cart_dict.items():
        new_dict[sku_id] = dict['count']

        if dict['selected']:
            new_add.append(sku_id)
        else:
            new_remove.append(sku_id)

    # 4.链接redis, 获取链接对象
    redis_conn = get_redis_connection('carts')

    # 5.往hash中增加数据  : dict={}
    redis_conn.hmset('carts_%s' % request.user.id, new_dict)

    # 6.判断add=[]中是否有值, 有的话: 往set中增加数据
    if new_add:
        redis_conn.sadd('selected_%s' % request.user.id, *new_add)

    # 7.判断remove=[]中是否有值, 有的话: 从set中删除数据
    if new_remove:
        redis_conn.srem('selected_%s' % request.user.id, *new_remove)

    # 8.删除cookie中的购物车记录
    response.delete_cookie('carts')

    # 9.返回结果
    return response



















