from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Artigo


@transaction.atomic
def cadastrar(titulo: str, resumo: str, arquivo) -> Artigo:
    """Cadastra um novo artigo."""

    artigo = Artigo(
        titulo=titulo,
        resumo=resumo,
        arquivo=arquivo,
        status="rascunho",
    )

    artigo.full_clean()
    artigo.save()

    return artigo


@transaction.atomic
def atualizar(artigo_id: int, titulo: str, resumo: str,
              arquivo=None) -> Artigo:
    """Atualiza os dados de um artigo existente."""

    try:
        artigo = Artigo.objects.get(pk=artigo_id)
    except Artigo.DoesNotExist:
        raise ValidationError("Artigo não encontrado.")

    artigo.titulo = titulo
    artigo.resumo = resumo

    if arquivo is not None:
        artigo.arquivo = arquivo

    artigo.full_clean()
    artigo.save()

    return artigo


@transaction.atomic
def excluir(artigo_id: int) -> None:
    """Exclui um artigo existente."""

    try:
        artigo = Artigo.objects.get(pk=artigo_id)
    except Artigo.DoesNotExist:
        raise ValidationError("Artigo não encontrado.")

    artigo.delete()


@transaction.atomic
def publicar(artigo_id: int) -> Artigo:
    """Publica um artigo e registra a data de publicação."""

    try:
        artigo = Artigo.objects.get(pk=artigo_id)
    except Artigo.DoesNotExist:
        raise ValidationError("Artigo não encontrado.")

    artigo.status = "publicado"
    artigo.data_publicacao = timezone.now()

    artigo.full_clean()
    artigo.save(update_fields=["status", "data_publicacao"])

    return artigo
