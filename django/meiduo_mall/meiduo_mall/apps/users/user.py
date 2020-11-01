from users import address

from users.models import User


def user_info(user_id):
    """
    这个函数返回用户信息
    参数说明: user_id
    返回值: {'username':'张三','mobile':'17812345678','default_address':{'title':'公司','mobile':'13812345678','place':'浦东新区航头镇108 号','receiver':'张三'}}
    """
    # 判断用户是否存在，不存在返回空字典
    user_count = User.objects.filter(id=user_id).count()
    if user_count == 0:
        return {}
    # 用户存在，查询这个用户
    user = User.objects.get(id=user_id)
    # 获取默认地址
    default_address = address.default(user_id)
    # 组装结果，并返回
    return {'username': user.username, 'mobile': user.mobile, 'default_address': default_address}