from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.AuthLoginView.as_view(), name='login'),
    path('logout/', views.AuthLogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
]
