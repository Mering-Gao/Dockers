from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
# Create your views here.
from goods.models import GoodsCategory, SKU
from goods.utils import get_breadcrumb


class ListView(View):


    def get(self, request, category_id):
        '''接收商品的三级分类id,获取对应的商品,排序后分页返回'''
        
        # 1.接收参数(查询字符串)
        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        ordering = request.GET.get('ordering')

        # 2.根据三级类别id, 获取对应的类别
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return JsonResponse({'code':400,
                                 'errmsg':'根据id获取类别出错'})


        # 根据category获取对应的面包屑效果数据:
        dict = get_breadcrumb(category)

        try:
            # 3.根据该类别,去商品表查询商品(该类别, 上架的), 安装前端传入的参数排序
            skus = SKU.objects.filter(category=category,
                               is_launched=True).order_by(ordering)
        except Exception as e:
            return JsonResponse({'code':400,
                                 'errmsg':'获取对应的商品出错'})

        # 4.根据分页类, 创建分页对象
        paginator = Paginator(skus, page_size)

        # 5.调用分页对象的page(页码),获取对应该页码的商品
        try:
            page_skus = paginator.page(page)
        except EmptyPage:
            return JsonResponse({'code': 400,
                                 'errmsg': 'page页码出错'})

        # 6.调用分页对象的num_pages: 获取总页码
        totoal_pages = paginator.num_pages

        list = []

        # 7.遍历获取对应该页码的商品, 拿取每一个, 拼接参数
        for sku in page_skus:
            list.append({
                'id':sku.id,
                'name':sku.name,
                'default_image_url':sku.default_image_url,
                'price':sku.price
            })

        # 8.整理格式, 返回
        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'breadcrumb':dict,
                             'list':list,
                             'count':totoal_pages})



class HotListView(View):

    def get(self, request, category_id):
        '''获取热销商品(2个)'''

        try:
            category = GoodsCategory.objects.get(id=category_id)


            # 1.根据category_id,去SKU表中获取对应的商品,按照热销排序, 截取前两个
            skus = SKU.objects.filter(category=category,
                               is_launched=True).order_by('-sales')[:2]

        except Exception as e:
            return JsonResponse({'code':400,
                                 'errmsg':'从数据库获取数据出错'})

        list = []

        # 2.遍历商品, 获取每一个  ====> {}  ===> []
        for sku in skus:
            list.append({
                'id':sku.id,
                'default_image_url':sku.default_image_url,
                'price':sku.price,
                'name':sku.name
            })

        # 3.拼接参数, 返回json
        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'hot_skus':list})


# 导入:
# from haystack.views import SearchView
#
# class MySearchView(SearchView):
#     '''重写SearchView类'''
#
#     def create_response(self):
#         page = self.request.GET.get('page')
#         # 获取搜索结果
#         context = self.get_context()
#         data_list = []
#         for sku in context['page'].object_list:
#             data_list.append({
#                 'id':sku.object.id,
#                 'name':sku.object.name,
#                 'price':sku.object.price,
#                 'default_image_url':sku.object.default_image_url,
#                 'searchkey':context.get('query'),
#                 'page_size':context['page'].paginator.num_pages,
#                 'count':context['page'].paginator.count
#             })
#         # 拼接参数, 返回
#         return JsonResponse(data_list, safe=False)
#
#















