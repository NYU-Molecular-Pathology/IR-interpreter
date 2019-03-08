from . import views

app_name = 'lims'

urlpatterns = [
    path('', views.HomeView.as_view(), name='index')
]
