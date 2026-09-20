from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from hrms.approval_views import handle_approval

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('employees/', include('employees.urls')),
    path('recruitment/', include('recruitment.urls')),
    path('training/', include('training.urls')),
    path('appraisals/', include('appraisals.urls')),
    path('leave/', include('leave.urls')),
    path('overtime/', include('overtime.urls')),
    path('attendance/', include('attendance.urls')),
    # Email approval links
    path('approval/<str:token>/', handle_approval, name='handle_approval'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
