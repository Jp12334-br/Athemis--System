from django.db import models


class Artigo(models.Model):
        titulo = models.CharField(max_length=255)
        resumo = models.TextField()
        arquivo = models.FileField(upload_to="artigos/")
        data_criacao = models.DateTimeField(auto_now_add=True)
        data_publicacao = models.DateTimeField(null=True, blank=True)
        status = models.CharField(max_length=30, default="rascunho")

        def __str__(self):
            return self.titulo
        


# Create your models here.
