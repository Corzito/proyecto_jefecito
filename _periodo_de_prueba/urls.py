from django.urls import path
from . import views

app_name = 'periodo'

urlpatterns = [
    path('', views.lista_colaboradores, name='lista'),
    path('agregar/', views.agregar_colaborador, name='agregar'),
    path('editar/<int:pk>/', views.editar_colaborador, name='editar'),
    path('eliminar/<int:pk>/', views.eliminar_colaborador, name='eliminar'),
    path('evaluacion/<int:pk>/<str:tipo>/', views.marcar_evaluacion, name='marcar_evaluacion'),
    path('plantilla-excel/', views.descargar_plantilla, name='descargar_plantilla'),
    path('carga-masiva/', views.carga_masiva, name='carga_masiva'),

    # ── Jefes Inmediatos ──────────────────────────────────────
    path('jefes/', views.lista_jefes, name='lista_jefes'),
    path('jefes/agregar/', views.agregar_jefe, name='agregar_jefe'),
    path('jefes/editar/<int:pk>/', views.editar_jefe, name='editar_jefe'),
    path('jefes/eliminar/<int:pk>/', views.eliminar_jefe, name='eliminar_jefe'),
]