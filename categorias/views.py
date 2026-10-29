from django.shortcuts import render
from .models import Categoria
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import service


@api_view(["POST"])
def cadastrar_categoria(request):
    """Cadastra uma nova categoria."""

    try:
        categoria = service.cadastrar(
            nome=request.data.get("nome", ""),
            slug=request.data.get("slug", ""),
            descricao=request.data.get("descricao", ""),
            categoria_pai_id=request.data.get("categoria_pai_id"),
        )

        return Response(
            {
                "mensagem": "Categoria cadastrada com sucesso.",
                "categoria": {
                    "id": categoria.id,
                    "nome": categoria.nome,
                    "descricao": categoria.descricao,
                    "slug": categoria.slug,
                    "categoria_pai_id": categoria.categoria_pai_id,
                    "data_criacao": categoria.data_criacao,
                    "ativa": categoria.ativa,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    except ValidationError as erro:
        return Response(
            {"erro": erro.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["GET"])
def listar_categorias(request):
    """Lista todas as categorias."""

    categorias = service.Categoria.objects.all()

    dados = [
        {
            "id": categoria.id,
            "nome": categoria.nome,
            "descricao": categoria.descricao,
            "slug": categoria.slug,
            "categoria_pai_id": categoria.categoria_pai_id,
            "data_criacao": categoria.data_criacao,
            "ativa": categoria.ativa,
        }
        for categoria in categorias
    ]

    return Response(dados, status=status.HTTP_200_OK)


@api_view(["GET"])
def detalhe_categoria(request, categoria_id):
    """Busca uma categoria pelo ID."""

    try:
        categoria = service.buscar_por_id(categoria_id)

        return Response(
            {
                "id": categoria.id,
                "nome": categoria.nome,
                "descricao": categoria.descricao,
                "slug": categoria.slug,
                "categoria_pai_id": categoria.categoria_pai_id,
                "data_criacao": categoria.data_criacao,
                "ativa": categoria.ativa,
            },
            status=status.HTTP_200_OK,
        )

    except ValidationError as erro:
        return Response(
            {"erro": erro.messages},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["PUT", "PATCH"])
def atualizar_categoria(request, categoria_id):
    """Atualiza uma categoria existente."""

    try:
        categoria = service.buscar_por_id(categoria_id)

        categoria = service.atualizar(
            categoria_id=categoria_id,
            nome=request.data.get("nome", categoria.nome),
            slug=request.data.get("slug", categoria.slug),
            descricao=request.data.get("descricao", categoria.descricao),
            categoria_pai_id=request.data.get(
                "categoria_pai_id",
                categoria.categoria_pai_id,
            ),
        )

        return Response(
            {
                "mensagem": "Categoria atualizada com sucesso.",
                "id": categoria.id,
                "nome": categoria.nome,
                "descricao": categoria.descricao,
                "slug": categoria.slug,
                "categoria_pai_id": categoria.categoria_pai_id,
                "data_criacao": categoria.data_criacao,
                "ativa": categoria.ativa,
            },
            status=status.HTTP_200_OK,
        )

    except ValidationError as erro:
        return Response(
            {"erro": erro.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["DELETE"])
def excluir_categoria(request, categoria_id):
    """Exclui uma categoria."""

    try:
        service.excluir(categoria_id)

        return Response(
            {"mensagem": "Categoria excluída com sucesso."},
            status=status.HTTP_204_NO_CONTENT,
        )

    except ValidationError as erro:
        return Response(
            {"erro": erro.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["PATCH"])
def desativar_categoria(request, categoria_id):
    """Desativa uma categoria."""

    try:
        categoria = service.desativar(categoria_id)

        return Response(
            {
                "mensagem": "Categoria desativada com sucesso.",
                "id": categoria.id,
                "nome": categoria.nome,
                "ativa": categoria.ativa,
            },
            status=status.HTTP_200_OK,
        )

    except ValidationError as erro:
        return Response(
            {"erro": erro.messages},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["GET"])
def listar_subcategorias(request, categoria_id):
    """Lista as subcategorias diretas de uma categoria."""

    try:
        subcategorias = service.listar_subcategorias(categoria_id)

        dados = [
            {
                "id": categoria.id,
                "nome": categoria.nome,
                "slug": categoria.slug,
                "categoria_pai_id": categoria.categoria_pai_id,
                "ativa": categoria.ativa,
            }
            for categoria in subcategorias
        ]

        return Response(dados, status=status.HTTP_200_OK)

    except ValidationError as erro:
        return Response(
            {"erro": erro.messages},
            status=status.HTTP_404_NOT_FOUND,
        )
# Create your views here.
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