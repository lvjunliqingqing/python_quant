
from django.urls import path
from rest_framework_jwt.views import obtain_jwt_token

from stock import views2, views1
from . import views
from stock.controller import common


urlpatterns = [
    path(r'condition', views1.condition),
    path(r'condition1', views2.condition),
    path(r'kline', views.kline_chart),
    path(r'condition_list', common.conditionList),
    path(r'dynamic_form_list', common.dynamicFormList),
]


