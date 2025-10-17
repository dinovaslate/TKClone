from django.urls import path

from . import views

app_name = 'payments'

urlpatterns = [
    path('receipt/<int:booking_id>/', views.receipt, name='receipt'),
]
