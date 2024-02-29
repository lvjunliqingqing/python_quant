from django.urls import path
from rest_framework_jwt.views import obtain_jwt_token

from . import views

urlpatterns = [
    path(r'', views.index),
    path(r'login', obtain_jwt_token),
    path(r'info', views.info),
    path(r'logout', views.logout),
    path(r'change_password', views.change_password),
]


