from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('recruitment/', include('recruitment.urls')),
    path('training/', include('training.urls')),
    path('appraisals/', include('appraisals.urls')),
    path('leave/', include('leave.urls')),
    path('overtime/', include('overtime.urls')),
    path('attendance/', include('attendance.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
