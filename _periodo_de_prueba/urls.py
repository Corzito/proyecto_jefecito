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
    path('importar/', views.importar_excel, name='importar'),
    path('enviar-jefe/<int:pk>/', views.enviar_alerta_jefe, name='enviar_alerta_jefe'),
]