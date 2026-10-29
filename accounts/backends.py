from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Permite autenticação informando username ou email junto com a senha.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        identificador = username or kwargs.get("email")
        if not identificador or not password:
            return None

        identificador = str(identificador).strip()

        try:
            user = User.objects.get(
                Q(username=identificador) | Q(email__iexact=identificador)
            )
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
