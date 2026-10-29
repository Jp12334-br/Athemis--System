from django.urls import path
from . import views

app_name = "categorias"

urlpatterns = [
    # Listar todas as categorias
    path("", views.listar_categorias, name="listar"),

    # Cadastrar uma categoria
    path("cadastrar/", views.cadastrar_categoria, name="cadastrar"),

    # Consultar uma categoria pelo ID
    path("<int:categoria_id>/", views.detalhe_categoria, name="detalhe"),

    # Atualizar uma categoria
    path(
        "<int:categoria_id>/atualizar/",
        views.atualizar_categoria,
        name="atualizar",
    ),

    # Excluir uma categoria
    path(
        "<int:categoria_id>/excluir/",
        views.excluir_categoria,
        name="excluir",
    ),

    # Desativar uma categoria
    path(
        "<int:categoria_id>/desativar/",
        views.desativar_categoria,
        name="desativar",
    ),

    # Listar as subcategorias
    path(
        "<int:categoria_id>/subcategorias/",
        views.listar_subcategorias,
        name="subcategorias",
    ),
]