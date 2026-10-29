from django.urls import path
from . import views

app_name = "articles"

urlpatterns = [
    path("", views.cadastrar_artigo, name="cadastrar_artigo"),
    path("int:artigo_id/", views.detalhe_artigo, name="detalhe_artigo"),
    path("int:artigo_id/excluir/", views.excluir_artigo, name="excluir_artigo"),
    path("int:artigo_id/publicar/", views.publicar_artigo, name="publicar_artigo"),
]