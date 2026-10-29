
from django.urls import path

from . import views

app_name = "feed"

urlpatterns = [
    # Listar artigos publicados
    path(
        "",
        views.listar_feed,
        name="listar",
    ),

    # Pesquisar artigos por título ou resumo
    path(
        "pesquisar/",
        views.pesquisar_feed,
        name="pesquisar",
    ),

    # Filtrar artigos por categoria e subcategorias
    path(
        "categoria/<int:categoria_id>/",
        views.filtrar_feed_categoria,
        name="filtrar_categoria",
    ),

    # Registrar a leitura de um artigo
    path(
        "ler/<int:artigo_id>/",
        views.registrar_leitura,
        name="registrar_leitura",
    ),

    # Recomendar artigos com base no histórico de leitura
    path(
        "recomendacoes/",
        views.recomendar_feed,
        name="recomendacoes",
    ),
]
