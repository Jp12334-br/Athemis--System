from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from articles.models import Artigo
from categorias.models import Categoria
from .models import LeituraArtigo


def _artigos_publicados():
    """
    Retorna somente artigos publicados.
    """
    return Artigo.objects.filter(
        status="publicado"
    )


def listar_artigos():
    """
    Lista os artigos publicados, dos mais recentes
    para os mais antigos.
    """
    return _artigos_publicados().order_by(
        "-data_publicacao",
        "-data_criacao"
    )


def pesquisar_artigos(termo):
    """
    Pesquisa artigos publicados pelo título ou resumo.
    """
    artigos = listar_artigos()

    termo = (termo or "").strip()

    if not termo:
        return artigos

    return artigos.filter(
        Q(titulo__icontains=termo)
        | Q(resumo__icontains=termo)
    ).distinct()


def _obter_ids_categoria_e_descendentes(categoria_id):
    """
    Retorna o ID da categoria selecionada e os IDs
    de todas as suas subcategorias, inclusive níveis
    mais profundos.
    """
    try:
        categoria = Categoria.objects.get(
            pk=categoria_id,
            ativa=True
        )
    except Categoria.DoesNotExist:
        raise ValidationError("Categoria não encontrada ou inativa.")

    ids_categorias = {categoria.pk}
    ids_pendentes = {categoria.pk}

    while ids_pendentes:
        ids_filhos = set(
            Categoria.objects.filter(
                categoria_pai_id__in=ids_pendentes,
                ativa=True
            ).values_list("id", flat=True)
        )

        novos_ids = ids_filhos - ids_categorias

        ids_categorias.update(novos_ids)
        ids_pendentes = novos_ids

    return ids_categorias


def filtrar_por_categoria(categoria_id):
    """
    Retorna artigos publicados associados à categoria
    selecionada ou a alguma de suas subcategorias.
    """
    ids_categorias = _obter_ids_categoria_e_descendentes(
        categoria_id
    )

    return (
        listar_artigos()
        .filter(categorias__id__in=ids_categorias)
        .distinct()
    )


def buscar_artigo_por_id(artigo_id):
    """
    Busca um artigo publicado pelo ID.
    """
    try:
        return _artigos_publicados().get(pk=artigo_id)
    except Artigo.DoesNotExist:
        raise ValidationError("Artigo publicado não encontrado.")


@transaction.atomic
def registrar_leitura(usuario, artigo_id):
    """
    Registra a leitura de um artigo por um usuário.

    Se o usuário já tiver lido esse artigo, atualiza
    a data da última leitura.
    """
    if not usuario or not usuario.is_authenticated:
        raise ValidationError(
            "É necessário estar autenticado para registrar uma leitura."
        )

    artigo = buscar_artigo_por_id(artigo_id)

    leitura, criada = LeituraArtigo.objects.update_or_create(
        usuario=usuario,
        artigo=artigo,
        defaults={
            "data_leitura": timezone.now()
        }
    )

    return leitura


def recomendar_artigos(usuario, limite=10, quantidade_leituras=10):
    """
    Recomenda artigos publicados com base nas categorias
    dos artigos lidos recentemente pelo usuário.

    Não recomenda artigos que o usuário já leu.
    """
    if not usuario or not usuario.is_authenticated:
        raise ValidationError(
            "É necessário estar autenticado para receber recomendações."
        )

    if limite < 1:
        raise ValidationError(
            "O limite de recomendações deve ser maior que zero."
        )

    if quantidade_leituras < 1:
        raise ValidationError(
            "A quantidade de leituras deve ser maior que zero."
        )

    leituras_recentes = (
        LeituraArtigo.objects
        .filter(usuario=usuario)
        .select_related("artigo")
        .prefetch_related("artigo__categorias")
        .order_by("-data_leitura")[:quantidade_leituras]
    )

    ids_artigos_lidos = set()
    ids_categorias = set()

    for leitura in leituras_recentes:
        ids_artigos_lidos.add(leitura.artigo_id)

        ids_categorias.update(
            leitura.artigo.categorias.values_list(
                "id",
                flat=True
            )
        )

    if not ids_categorias:
        return Artigo.objects.none()

    recomendacoes = (
        listar_artigos()
        .filter(categorias__id__in=ids_categorias)
        .exclude(id__in=ids_artigos_lidos)
        .distinct()
        .order_by("-data_publicacao", "-data_criacao")
    )

    return recomendacoes[:limite]