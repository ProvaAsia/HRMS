from django.urls import path
from . import views

urlpatterns = [
    path('', views.leave_dashboard, name='leave_dashboard'),
    path('requests/', views.request_list, name='leave_list'),
    path('requests/create/', views.request_create, name='leave_create'),
    path('requests/<int:pk>/', views.request_detail, name='leave_detail'),
    path('requests/<int:pk>/cancel/', views.request_cancel, name='leave_cancel'),
    path('types/', views.leave_type_list, name='leave_type_list'),
    path('balances/', views.balance_list, name='leave_balance_list'),
]
