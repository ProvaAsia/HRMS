from django.urls import path
from . import views

urlpatterns = [
    path('', views.ot_dashboard, name='ot_dashboard'),
    path('requests/', views.ot_list, name='ot_list'),
    path('requests/create/', views.ot_create, name='ot_create'),
    path('requests/<int:pk>/', views.ot_detail, name='ot_detail'),
    path('requests/<int:pk>/cancel/', views.ot_cancel, name='ot_cancel'),
]
