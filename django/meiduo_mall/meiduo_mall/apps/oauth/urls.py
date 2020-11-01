from django.conf.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^qq/authorization/$', views.QQURLView.as_view()),
    re_path(r'^oauth_callback/$', views.QQURLSecondView.as_view()),
]