from django.core.cache import cache
from django.views import View
from .models import Area
from django.http import JsonResponse


class ProvinceView(View):

    def get(self, request):
        '''前端发送请求,获取省份数据'''

        list = cache.get('province')

        if not list:

            try:
                # 1.查询省级数据
                province_model_list = Area.objects.filter(parent__isnull=True)

                # 创建一个list:
                list = []

                # 2.整理省级数据
                for province in province_model_list:
                    list.append({
                        'id':province.id,
                        'name':province.name
                    })

                cache.set('province', list, 3600)

            except Exception as e:
                # 如果报错, 则返回错误原因:
                return JsonResponse({'code':400,
                                     'errmsg':"获取省份数据出错"})


        # 3.返回整理好的省级数据
        return JsonResponse({'code':0,
                             'errmsg':"ok",
                             'province_list':list})


class SubAreaView(View):


    def get(self, request, pk):
        '''接收pk值, 通过pk值,获取对应的对象, 还要获取pk对应的下一级数据对象'''

        dict = cache.get('sub_data_%s' % pk)

        if not dict:

            try:
                # 1.根据pk获取对应的对象
                province = Area.objects.get(id=pk)

                # 2.获取pk对应的下一级所有的数据对象
                sub_model_list = Area.objects.filter(parent=pk)

                list = []

                # 3.遍历下一级所有的数据对象, 获取每一个
                for sub_model in sub_model_list:
                    # 4.把每一个对象 ===> {} ===> []
                    list.append({
                        'id':sub_model.id,
                        'name':sub_model.name
                    })

                # 5.再创建一个dict, 把dict整理好
                dict = {
                    'id':province.id,
                    'name':province.name,
                    'subs':list
                }

                cache.set('sub_data_' + pk, dict, 3600)
            except Exception as e:
                return JsonResponse({'code':400,
                                     'errmsg':'获取不到数据'})

        # 6.整理json返回.
        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'sub_data':dict})




























