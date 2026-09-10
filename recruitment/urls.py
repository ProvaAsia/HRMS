from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('jobs/<int:pk>/delete/', views.job_delete, name='job_delete'),
    path('candidates/', views.candidate_list, name='candidate_list'),
    path('candidates/create/', views.candidate_create, name='candidate_create'),
    path('candidates/<int:pk>/', views.candidate_detail, name='candidate_detail'),
    path('candidates/<int:pk>/edit/', views.candidate_edit, name='candidate_edit'),
    path('candidates/<int:pk>/delete/', views.candidate_delete, name='candidate_delete'),
]
