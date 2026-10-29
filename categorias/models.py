from django.db import models


class Categoria(models.Model):

    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nome"
    )

    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição"
    )

    slug = models.SlugField(
        max_length=120,
        unique=True,
        verbose_name="Slug"
    )

    categoria_pai = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="subcategorias",
        verbose_name="Categoria pai"
    )

    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de criação"
    )

    ativa = models.BooleanField(
        default=True,
        verbose_name="Ativa"
    )

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["nome"]

    def __str__(self):
        return self.nome