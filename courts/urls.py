from django.urls import path

from . import views

app_name = 'courts'

urlpatterns = [
    path('', views.court_list, name='list'),
    path('<int:pk>/', views.court_detail, name='detail'),
]
