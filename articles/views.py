
from django.core.exceptions import ValidationError
from django.http import Http404

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response

from .models import Artigo
from . import service


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def cadastrar_artigo(request):
    """Cadastra um artigo."""

    titulo = request.data.get("titulo")
    resumo = request.data.get("resumo", "")
    arquivo = request.FILES.get("arquivo")

    if not titulo:
        return Response(
            {"erro": "O título é obrigatório."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not arquivo:
        return Response(
            {"erro": "O arquivo do artigo é obrigatório."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        artigo = service.cadastrar(
            titulo=titulo,
            resumo=resumo,
            arquivo=arquivo,
        )
    except ValidationError as erro:
        return Response(
            {"erro": erro.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "mensagem": "Artigo cadastrado com sucesso.",
            "artigo": {
                "id": artigo.id,
                "titulo": artigo.titulo,
                "resumo": artigo.resumo,
                "data_criacao": artigo.data_criacao,
                "status": artigo.status,
            },
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PATCH"])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def detalhe_artigo(request, artigo_id):
    """Consulta ou atualiza um artigo."""

    try:
        artigo = service.buscar_artigo_por_id(artigo_id)
    except ValidationError:
        raise Http404("Artigo não encontrado.")

    if request.method == "GET":
        return Response({
            "id": artigo.id,
            "titulo": artigo.titulo,
            "resumo": artigo.resumo,
            "arquivo": artigo.arquivo.url if artigo.arquivo else None,
            "data_criacao": artigo.data_criacao,
            "data_publicacao": artigo.data_publicacao,
            "status": artigo.status,
        })

    titulo = request.data.get("titulo", artigo.titulo)
    resumo = request.data.get("resumo", artigo.resumo)
    arquivo = request.FILES.get("arquivo")

    try:
        artigo = service.atualizar(
            artigo_id=artigo_id,
            titulo=titulo,
            resumo=resumo,
            arquivo=arquivo,
        )
    except ValidationError as erro:
        return Response(
            {"erro": erro.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({
        "mensagem": "Artigo atualizado com sucesso.",
        "id": artigo.id,
        "titulo": artigo.titulo,
        "resumo": artigo.resumo,
    })


@api_view(["DELETE"])
def excluir_artigo(request, artigo_id):
    """Exclui um artigo."""

    try:
        service.excluir(artigo_id)
    except ValidationError:
        raise Http404("Artigo não encontrado.")

    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def publicar_artigo(request, artigo_id):
    """Publica um artigo."""

    try:
        artigo = service.publicar(artigo_id)
    except ValidationError as erro:
        return Response(
            {"erro": erro.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({
        "mensagem": "Artigo publicado com sucesso.",
        "id": artigo.id,
        "titulo": artigo.titulo,
        "status": artigo.status,
        "data_publicacao": artigo.data_publicacao,
    })
