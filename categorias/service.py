from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Categoria


@transaction.atomic
def cadastrar(
    nome: str,
    slug: str,
    descricao: str = "",
    categoria_pai_id: int | None = None,
) -> Categoria:
    """
    Cadastra uma nova categoria.
    """

    categoria = Categoria(
        nome=nome.strip(),
        slug=slug.strip(),
        descricao=descricao.strip(),
        categoria_pai_id=categoria_pai_id,
        ativa=True,
    )

    validar_hierarquia(categoria)

    categoria.full_clean()
    categoria.save()

    return categoria


@transaction.atomic
def atualizar(
    categoria_id: int,
    nome: str,
    slug: str,
    descricao: str = "",
    categoria_pai_id: int | None = None,
) -> Categoria:
    """
    Atualiza os dados de uma categoria existente.
    """

    categoria = buscar_por_id(categoria_id)

    categoria.nome = nome.strip()
    categoria.slug = slug.strip()
    categoria.descricao = descricao.strip()
    categoria.categoria_pai_id = categoria_pai_id

    validar_hierarquia(categoria)

    categoria.full_clean()
    categoria.save()

    return categoria


@transaction.atomic
def excluir(categoria_id: int) -> None:
    """
    Exclui uma categoria, desde que não existam
    subcategorias ou outros relacionamentos que impeçam a exclusão.
    """

    categoria = buscar_por_id(categoria_id)
    categoria.delete()


@transaction.atomic
def desativar(categoria_id: int) -> Categoria:
    """
    Desativa uma categoria sem excluir seu registro.
    """

    categoria = buscar_por_id(categoria_id)

    categoria.ativa = False
    categoria.save(update_fields=["ativa"])

    return categoria


def buscar_por_id(categoria_id: int) -> Categoria:
    """
    Busca uma categoria pelo identificador.
    """

    try:
        return Categoria.objects.get(pk=categoria_id)
    except Categoria.DoesNotExist:
        raise ValidationError("Categoria não encontrada.")


def listar_subcategorias(categoria_id: int):
    """
    Retorna as subcategorias diretas de uma categoria.
    """

    categoria = buscar_por_id(categoria_id)

    return categoria.subcategorias.all()


def validar_hierarquia(categoria: Categoria) -> None:
    """
    Impede que uma categoria seja sua própria categoria pai
    ou que a hierarquia crie um ciclo.
    """

    if categoria.categoria_pai_id is None:
        return

    if categoria.pk == categoria.categoria_pai_id:
        raise ValidationError(
            "Uma categoria não pode ser sua própria categoria pai."
        )

    pai = buscar_por_id(categoria.categoria_pai_id)

    while pai is not None:
        if categoria.pk is not None and pai.pk == categoria.pk:
            raise ValidationError(
                "Essa alteração criaria um ciclo na hierarquia."
            )

        pai = pai.categoria_pai

    if not pai and categoria.categoria_pai_id is None:
        return