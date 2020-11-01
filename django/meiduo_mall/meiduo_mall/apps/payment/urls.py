from django.conf.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^payment/(?P<order_id>\d+)/$', views.PaymentsView.as_view()),
]