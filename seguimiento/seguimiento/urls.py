from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('periodo-prueba/', include('_periodo_de_prueba.urls')),
    path('', lambda request: redirect('periodo-prueba/')),
]