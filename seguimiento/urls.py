from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('periodo-prueba/', include('_periodo_de_prueba.urls')),
    path('', RedirectView.as_view(url='/periodo-prueba/', permanent=False)),
]