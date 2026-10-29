from django.shortcuts import render

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from . import service


@api_view(["GET"])
@permission_classes([AllowAny])
def listar_feed(request):
    """
    Retorna os artigos publicados, começando pelos mais recentes.
    """
    artigos = service.listar_artigos()

    dados = [
        {
            "id": artigo.id,
            "titulo": artigo.titulo,
            "resumo": artigo.resumo,
            "data_publicacao": (
                artigo.data_publicacao.isoformat()
                if artigo.data_publicacao
                else None
            ),
        }
        for artigo in artigos
    ]

    return Response(dados, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def pesquisar_feed(request):
    """
    Pesquisa artigos pelo título ou resumo.
    """
    termo = request.query_params.get("q", "")

    artigos = service.pesquisar_artigos(termo)

    dados = [
        {
            "id": artigo.id,
            "titulo": artigo.titulo,
            "resumo": artigo.resumo,
            "data_publicacao": (
                artigo.data_publicacao.isoformat()
                if artigo.data_publicacao
                else None
            ),
        }
        for artigo in artigos
    ]

    return Response(dados, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def filtrar_feed_categoria(request, categoria_id):
    """
    Retorna artigos publicados da categoria selecionada
    ou de suas subcategorias.
    """
    try:
        artigos = service.filtrar_por_categoria(categoria_id)

        dados = [
            {
                "id": artigo.id,
                "titulo": artigo.titulo,
                "resumo": artigo.resumo,
                "data_publicacao": (
                    artigo.data_publicacao.isoformat()
                    if artigo.data_publicacao
                    else None
                ),
            }
            for artigo in artigos
        ]

        return Response(dados, status=status.HTTP_200_OK)

    except ValidationError as erro:
        return Response(
            {"erro": erro.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def registrar_leitura(request, artigo_id):
    """
    Registra a leitura de um artigo pelo usuário autenticado.
    """
    try:
        leitura = service.registrar_leitura(
            usuario=request.user,
            artigo_id=artigo_id,
        )

        return Response(
            {
                "mensagem": "Leitura registrada com sucesso.",
                "artigo_id": leitura.artigo_id,
                "data_leitura": leitura.data_leitura.isoformat(),
            },
            status=status.HTTP_200_OK,
        )

    except ValidationError as erro:
        return Response(
            {"erro": erro.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recomendar_feed(request):
    """
    Recomenda artigos com base nas categorias dos artigos
    lidos recentemente pelo usuário.
    """
    try:
        limite = int(request.query_params.get("limite", 10))
        quantidade_leituras = int(
            request.query_params.get("quantidade_leituras", 10)
        )

        artigos = service.recomendar_artigos(
            usuario=request.user,
            limite=limite,
            quantidade_leituras=quantidade_leituras,
        )

        dados = [
            {
                "id": artigo.id,
                "titulo": artigo.titulo,
                "resumo": artigo.resumo,
                "data_publicacao": (
                    artigo.data_publicacao.isoformat()
                    if artigo.data_publicacao
                    else None
                ),
            }
            for artigo in artigos
        ]

        return Response(dados, status=status.HTTP_200_OK)

    except ValueError:
        return Response(
            {
                "erro": (
                    "Os parâmetros limite e quantidade_leituras "
                    "devem ser números inteiros."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    except ValidationError as erro:
        return Response(
            {"erro": erro.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )

# Create your views here.
