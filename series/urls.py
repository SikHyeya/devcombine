from django.contrib import admin
from django.urls import path, include
from . import views

app_name = 'series'

urlpatterns = [
    path('', views.main_series, name='main_series'),
    path('<int:series_id>/', views.series_course, name='series_course')
]
