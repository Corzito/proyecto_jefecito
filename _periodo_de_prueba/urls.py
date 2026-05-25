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
    path('ejecutar-alertas/', views.ejecutar_alertas, name='ejecutar_alertas'),
    path('primer-periodo/', views.primer_periodo, name='primer_periodo'),
    path('segundo-periodo/', views.segundo_periodo, name='segundo_periodo'),
    path('completados/', views.completados, name='completados'),
    path('resultado/<int:pk>/', views.marcar_resultado, name='marcar_resultado'),
]