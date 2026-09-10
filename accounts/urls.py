from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/users/', views.user_list, name='user_list'),
    path('accounts/users/create/', views.user_create, name='user_create'),
    path('accounts/users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('accounts/users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('accounts/invite/', views.invite_user, name='invite_user'),
    path('accounts/activate/<str:token>/', views.activate_account, name='activate_account'),
]
