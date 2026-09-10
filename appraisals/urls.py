from django.urls import path
from . import views

urlpatterns = [
    path('', views.cycle_list, name='appraisal_cycle_list'),
    path('cycles/create/', views.cycle_create, name='appraisal_cycle_create'),
    path('cycles/<int:pk>/', views.cycle_detail, name='appraisal_cycle_detail'),
    path('cycles/<int:pk>/edit/', views.cycle_edit, name='appraisal_cycle_edit'),
    path('appraisals/<int:pk>/', views.appraisal_detail, name='appraisal_detail'),
    path('my/', views.my_appraisals, name='my_appraisals'),
    path('goals/<int:pk>/update/', views.goal_update, name='goal_update'),
    path('goals/<int:pk>/delete/', views.goal_delete, name='goal_delete'),
]
