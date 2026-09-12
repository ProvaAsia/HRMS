from django.urls import path
from . import views
from . import views_masterdata

urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    path('my-profile/', views.employee_my_profile, name='employee_my_profile'),
    path('org-chart/', views.org_chart, name='org_chart'),
    path('create/', views.employee_create, name='employee_create'),
    path('<int:pk>/', views.employee_detail, name='employee_detail'),
    path('<int:pk>/edit/', views.employee_edit, name='employee_edit'),

    # ── Master Data ───────────────────────────────────────────
    path('masterdata/', views_masterdata.masterdata_overview, name='masterdata_overview'),
    path('masterdata/excel-template/', views_masterdata.masterdata_excel_template, name='masterdata_excel_template'),
    path('masterdata/excel-upload/', views_masterdata.masterdata_excel_upload, name='masterdata_excel_upload'),

    path('masterdata/division/create/', views_masterdata.division_create, name='division_create'),
    path('masterdata/division/<int:pk>/edit/', views_masterdata.division_edit, name='division_edit'),
    path('masterdata/division/<int:pk>/delete/', views_masterdata.division_delete, name='division_delete'),

    path('masterdata/department/create/', views_masterdata.department_create, name='department_create'),
    path('masterdata/department/<int:pk>/edit/', views_masterdata.department_edit, name='department_edit'),
    path('masterdata/department/<int:pk>/delete/', views_masterdata.department_delete, name='department_delete'),

    path('masterdata/costcenter/create/', views_masterdata.costcenter_create, name='costcenter_create'),
    path('masterdata/costcenter/<int:pk>/edit/', views_masterdata.costcenter_edit, name='costcenter_edit'),
    path('masterdata/costcenter/<int:pk>/delete/', views_masterdata.costcenter_delete, name='costcenter_delete'),

    path('masterdata/worklocation/create/', views_masterdata.worklocation_create, name='worklocation_create'),
    path('masterdata/worklocation/<int:pk>/edit/', views_masterdata.worklocation_edit, name='worklocation_edit'),
    path('masterdata/worklocation/<int:pk>/delete/', views_masterdata.worklocation_delete, name='worklocation_delete'),
]
