from django.http import JsonResponse

def my_decorator(func):
    '''判断用户是否登录, 如果登录, 执行func, 未登录, 返回json'''
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            # 进入: 说明是登录用户
            return func(request, *args, **kwargs)
        else:
            # 进入这里: 说明是匿名用户(未登录用户)
            return JsonResponse({'code':400,
                                 'errmsg':'请登录后重试'})
    return wrapper



class LoginRequiredMixin(object):
    '''定义一个用与判断是否登录的Mixin扩展类'''

    @classmethod
    def as_view(cls, *args, **kwargs):
        view = super().as_view(*args, **kwargs)
        return my_decorator(view)