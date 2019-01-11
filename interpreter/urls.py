from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'interpreter'

urlpatterns = [
    path('', views.index, name='index'),
    path('demo', views.demo, name='demo'),
    # path('samplesheet/upload', views.samplesheet_upload, name='samplesheet_upload')
]
