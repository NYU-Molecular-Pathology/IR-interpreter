from . import views

app_name = 'interpreter'

urlpatterns = [
    path('', views.index, name='index')
]
