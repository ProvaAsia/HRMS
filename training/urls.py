from django.urls import path
from . import views

urlpatterns = [
    path('', views.training_list, name='training_list'),
    path('create/', views.training_create, name='training_create'),
    path('<int:pk>/', views.training_detail, name='training_detail'),
    path('<int:pk>/edit/', views.training_edit, name='training_edit'),
    path('<int:pk>/delete/', views.training_delete, name='training_delete'),
    path('my/', views.my_trainings, name='my_trainings'),
    path('enrollment/<int:pk>/update/', views.enrollment_update, name='enrollment_update'),
    path('enrollment/<int:pk>/delete/', views.enrollment_delete, name='enrollment_delete'),
]
