from .models import Calc_etc
from . import views
from django.urls import path

urlpatterns = [
    path('', views.calc_ave, name='calc_ave'),
]