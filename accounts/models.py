from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    email = models.EmailField(
        max_length=255,
        unique=True
    )
    description = models.TextField(
        max_length=350,
        blank=True
    )

    def __str__(self):
        return self.username


class Institution(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )
    slug = models.SlugField(unique=True)
    site = models.URLField(
        max_length=100,
        blank=True
    )
    description = models.TextField(
        max_length=350,
        blank=True
    )
    verificada = models.BooleanField(default=False)
    data_entrada = models.DateField(auto_now_add=True)
    location = models.CharField(
        max_length=100,
        blank=True
    )

    cep = models.CharField(
    max_length=9,
    blank=True,
    default="",
    verbose_name="CEP")

    def __str__(self):
        return self.name


class Vinculo_instituicao(models.Model):

    class Cargo(models.TextChoices):
        MEMBRO = 'MEMBRO', 'Membro'
        PESQUISADOR = 'PESQUISADOR', 'Pesquisador'
        ADMINISTRADOR = 'ADMIN', 'Administrador'

    class Status(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        ATIVO = 'ATIVO', 'Ativo'
        RECUSADO = 'RECUSADO', 'Recusado'

    user_key = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vinculos_institucionais'
    )

    institution_key = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name='vinculos'
    )

    data_vinculo = models.DateField(auto_now_add=True)

    email_instituicao = models.EmailField(
        max_length=100,
        blank=True
    )

    cargo = models.CharField(
        max_length=20,
        choices=Cargo.choices,
        default=Cargo.MEMBRO
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDENTE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user_key', 'institution_key'],
                name='unique_user_institution'
            )
        ]

    def __str__(self):
        return f'{self.user_key.username} - {self.institution_key.name}'

class Departamento(models.Model):
    nome = models.CharField(max_length=150)

    email_institucional = models.EmailField(
        max_length=254,
        blank=True
    )

    instituicao = models.ForeignKey(
        "Institution",
        on_delete=models.CASCADE,
        related_name="departamentos"
    )

    usuarios = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="departamentos"
    )

    data_entrada = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["instituicao", "nome"],
                name="unique_departamento_por_instituicao"
            )
        ]
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} - {self.instituicao.nome}"    
