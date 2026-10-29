from django.db import models
from django.conf import settings
from django.db import models

from articles.models import Artigo


class LeituraArtigo(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="leituras_artigos",
        verbose_name="Usuário"
    )

    artigo = models.ForeignKey(
        Artigo,
        on_delete=models.CASCADE,
        related_name="leituras",
        verbose_name="Artigo"
    )

    data_leitura = models.DateTimeField(
        auto_now=True,
        verbose_name="Data da última leitura"
    )

    class Meta:
        verbose_name = "Leitura de artigo"
        verbose_name_plural = "Leituras de artigos"
        ordering = ["-data_leitura"]

        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "artigo"],
                name="unica_leitura_por_usuario_artigo"
            )
        ]

    def __str__(self):
        return f"{self.usuario} leu {self.artigo}"

# Create your models here.
