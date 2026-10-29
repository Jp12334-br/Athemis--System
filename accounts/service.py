from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import URLValidator, validate_email
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils.text import slugify
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from accounts.models import Institution, Vinculo_instituicao

User = get_user_model()


# ==========================================
# AUTENTICAÇÃO E JWT
# ==========================================

def autenticar_usuario(identificador, password):
    """
    Autentica o usuário aceitando username ou email junto com a senha.
    Lança ValidationError em caso de credenciais inválidas ou conta inativa.
    """
    identificador = (identificador or "").strip()
    password = (password or "").strip()

    if not identificador or not password:
        raise ValidationError("Usuário/e-mail e senha são obrigatórios.")

    usuario = User.objects.filter(
        Q(username=identificador) | Q(email__iexact=identificador)
    ).first()

    if usuario is None or not usuario.check_password(password):
        raise ValidationError("Credenciais inválidas.")

    if not usuario.is_active:
        raise ValidationError("Esta conta está desativada.")

    return usuario


def gerar_tokens_para_usuario(usuario):
    """
    Gera o par de tokens JWT (refresh e access) para o usuário informado.
    """
    refresh = RefreshToken.for_user(usuario)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def login_usuario(identificador, password):
    """
    Executa o login do usuário aceitando username ou email com senha,
    retornando o usuário e o par de tokens JWT.
    """
    usuario = autenticar_usuario(identificador, password)
    tokens = gerar_tokens_para_usuario(usuario)
    return usuario, tokens


def renovar_token_acesso(refresh_token):
    """
    Recebe um refresh token e retorna um novo token de acesso JWT.
    """
    if not refresh_token:
        raise ValidationError("O token de atualização (refresh) é obrigatório.")

    try:
        token = RefreshToken(refresh_token)
        return {
            "access": str(token.access_token),
        }
    except TokenError as erro:
        raise ValidationError(f"Token de atualização inválido ou expirado: {str(erro)}")


def revogar_token(refresh_token):
    """
    Revoga o refresh token adicionando-o à lista de tokens bloqueados (blacklist).
    """
    if not refresh_token:
        raise ValidationError("O token de atualização (refresh) é obrigatório.")

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return True
    except TokenError as erro:
        raise ValidationError(f"Não foi possível revogar o token: {str(erro)}")


# ==========================================
# GERENCIAMENTO DE USUÁRIOS
# ==========================================

def cadastrar_usuario(username, email, password, description=""):
    """
    Cadastra um novo usuário comum no Athenis.
    Garante que usuários comuns não possam definir privilégios administrativos.
    """
    username = (username or "").strip()
    email = (email or "").strip().lower()
    description = (description or "").strip()

    if not username:
        raise ValidationError("O nome de usuário é obrigatório.")

    if not password:
        raise ValidationError("A senha é obrigatória.")

    try:
        validate_email(email)
    except ValidationError:
        raise ValidationError("O endereço de e-mail é inválido.")

    if User.objects.filter(username=username).exists():
        raise ValidationError("Nome de usuário já cadastrado.")

    if User.objects.filter(email__iexact=email).exists():
        raise ValidationError("E-mail já cadastrado.")

    if len(description) > 350:
        raise ValidationError("A descrição não pode ultrapassar 350 caracteres.")

    # Criação garantindo is_staff=False e is_superuser=False para usuários cadastrados
    usuario = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        description=description,
        is_staff=False,
        is_superuser=False,
    )

    return usuario


def buscar_usuario(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None


def buscar_usuario_por_email(email):
    try:
        return User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return None


def buscar_usuario_por_username(username):
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        return None


def atualizar_perfil(
    user_id,
    username=None,
    email=None,
    description=None,
    solicitante=None,
    dados_extras=None,
):
    """
    Atualiza dados do perfil de um usuário.
    Garante que cada usuário só possa alterar os próprios dados (exceto superusers)
    e que usuários comuns não possam definir privilégios administrativos.
    """
    try:
        usuario = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise ValidationError("Usuário não encontrado.")

    # 1. Garante que cada usuário só altere seus próprios dados
    if solicitante is not None:
        if solicitante.id != usuario.id and not solicitante.is_superuser:
            raise PermissionDenied("Você só tem permissão para alterar os seus próprios dados.")

    # 2. Garante que usuários comuns não possam definir privilégios administrativos
    if dados_extras:
        campos_admin = {"is_staff", "is_superuser", "is_admin"}
        if any(campo in dados_extras for campo in campos_admin):
            if solicitante is None or not solicitante.is_superuser:
                raise PermissionDenied("Usuários comuns não podem definir privilégios administrativos.")

    # 3. Atualizar o nome de usuário, se informado
    if username is not None:
        username = username.strip()

        if not username:
            raise ValidationError("O nome de usuário não pode ficar vazio.")

        if User.objects.filter(
            username__iexact=username
        ).exclude(id=usuario.id).exists():
            raise ValidationError("Este nome de usuário já está em uso.")

        usuario.username = username

    # 4. Atualizar o e-mail, se informado
    if email is not None:
        email = email.strip().lower()

        if not email:
            raise ValidationError("O e-mail não pode ficar vazio.")

        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("O endereço de e-mail é inválido.")

        if User.objects.filter(
            email__iexact=email
        ).exclude(id=usuario.id).exists():
            raise ValidationError("Este e-mail já está em uso.")

        usuario.email = email

    # 5. Atualizar a descrição, se informada
    if description is not None:
        description = description.strip()

        if len(description) > 350:
            raise ValidationError(
                "A descrição não pode ultrapassar 350 caracteres."
            )

        usuario.description = description

    usuario.save()
    return usuario


def alterar_email(user_id, novo_email):
    novo_email = novo_email.strip()

    try:
        validate_email(novo_email)
    except ValidationError:
        raise ValidationError("O endereço de e-mail informado é inválido.")

    novo_email = novo_email.lower()

    try:
        with transaction.atomic():
            usuario = User.objects.select_for_update().get(id=user_id)

            email_existente = User.objects.filter(
                email__iexact=novo_email
            ).exclude(id=usuario.id).exists()

            if email_existente:
                raise ValidationError(
                    "Este e-mail já está sendo utilizado por outra conta."
                )

            usuario.email = novo_email
            usuario.save(update_fields=["email"])

            return usuario

    except User.DoesNotExist:
        raise ValidationError("Usuário não encontrado.")
    except IntegrityError:
        raise ValidationError(
            "Não foi possível atualizar o e-mail. "
            "Verifique se ele já está sendo utilizado."
        )


def desativar_conta(user_id, solicitante=None):
    """
    Desativa a conta do usuário. Garante que apenas o próprio usuário (ou superuser)
    possa desativar a sua conta.
    """
    try:
        usuario = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise ValidationError("Usuário não encontrado.")

    if solicitante is not None and solicitante.id != usuario.id and not solicitante.is_superuser:
        raise PermissionDenied("Você só pode desativar a sua própria conta.")

    if not usuario.is_active:
        raise ValidationError("Esta conta já está desativada.")

    usuario.is_active = False
    usuario.save(update_fields=["is_active"])

    return usuario


# ==========================================
# GERENCIAMENTO DE INSTITUIÇÃO
# ==========================================

def cadastrar_instituicao(
    name,
    site="",
    description="",
    location="",
    criador=None,
):
    name = (name or "").strip()

    if not name:
        raise ValidationError("O nome da instituição é obrigatório.")

    if Institution.objects.filter(name__iexact=name).exists():
        raise ValidationError("Já existe uma instituição com esse nome.")

    slug = slugify(name)

    if not slug:
        raise ValidationError("Não foi possível gerar o identificador da instituição.")

    if Institution.objects.filter(slug=slug).exists():
        raise ValidationError("Já existe uma instituição com esse identificador.")

    site = (site or "").strip()
    if site:
        try:
            URLValidator()(site)
        except ValidationError:
            raise ValidationError("O endereço do site informado é inválido.")

    try:
        with transaction.atomic():
            instituicao = Institution.objects.create(
                name=name,
                slug=slug,
                site=site,
                description=(description or "").strip(),
                location=(location or "").strip(),
            )

            # Quando um usuário autenticado cria a instituição, torna-se o primeiro administrador ativo
            if criador is not None:
                Vinculo_instituicao.objects.create(
                    user_key=criador,
                    institution_key=instituicao,
                    cargo=Vinculo_instituicao.Cargo.ADMINISTRADOR,
                    status=Vinculo_instituicao.Status.ATIVO,
                )

    except IntegrityError:
        raise ValidationError(
            "Não foi possível cadastrar a instituição. "
            "Verifique se ela já existe."
        )

    return instituicao


def buscar_instituicao(institution_id):
    try:
        return Institution.objects.get(id=institution_id)
    except Institution.DoesNotExist:
        raise ValidationError("Instituição não encontrada.")


def listar_instituicoes():
    return Institution.objects.all().order_by("name")


# ==========================================
# GERENCIAMENTO DE VÍNCULOS INSTITUCIONAIS
# ==========================================

def _obter_vinculo(vinculo_id):
    try:
        return Vinculo_instituicao.objects.get(id=vinculo_id)
    except Vinculo_instituicao.DoesNotExist:
        raise ValidationError("Vínculo não encontrado.")


def _exigir_administrador(usuario, instituicao):
    """
    Verifica se o usuário é administrador ativo da instituição (ou superuser).
    """
    if getattr(usuario, "is_superuser", False):
        return

    autorizado = Vinculo_instituicao.objects.filter(
        user_key=usuario,
        institution_key=instituicao,
        cargo=Vinculo_instituicao.Cargo.ADMINISTRADOR,
        status=Vinculo_instituicao.Status.ATIVO,
    ).exists()

    if not autorizado:
        raise PermissionDenied("Você não tem permissão para administrar esta instituição.")


def solicitar_vinculo(user, institution, email_instituicao=""):
    """
    Cria uma solicitação de vínculo de um usuário com uma instituição.
    """
    if not user.is_active:
        raise ValidationError("Usuários desativados não podem solicitar vínculos.")

    if Vinculo_instituicao.objects.filter(
        user_key=user,
        institution_key=institution,
    ).exists():
        raise ValidationError(
            "Este usuário já possui um registro de vínculo com esta instituição."
        )

    try:
        with transaction.atomic():
            return Vinculo_instituicao.objects.create(
                user_key=user,
                institution_key=institution,
                email_instituicao=(email_instituicao or "").strip(),
                cargo=Vinculo_instituicao.Cargo.MEMBRO,
                status=Vinculo_instituicao.Status.PENDENTE,
            )
    except IntegrityError:
        raise ValidationError(
            "Não foi possível solicitar o vínculo. "
            "Verifique se já existe uma solicitação."
        )


def buscar_vinculo(vinculo_id):
    return _obter_vinculo(vinculo_id)


def listar_vinculos_usuario(user, status=None):
    vinculos = Vinculo_instituicao.objects.filter(
        user_key=user
    ).select_related("institution_key")

    if status is not None:
        vinculos = vinculos.filter(status=status)

    return vinculos.order_by("institution_key__name")


def listar_membros_instituicao(
    institution,
    status=Vinculo_instituicao.Status.ATIVO,
    solicitante=None,
):
    """
    Lista membros de uma instituição.
    Acesso a solicitações PENDENTES ou RECUSADAS exige permissão de administrador da instituição.
    """
    if status in [Vinculo_instituicao.Status.PENDENTE, Vinculo_instituicao.Status.RECUSADO]:
        if solicitante is not None and not solicitante.is_superuser:
            _exigir_administrador(solicitante, institution)

    vinculos = Vinculo_instituicao.objects.filter(
        institution_key=institution,
        status=status,
    ).select_related("user_key")

    return vinculos.order_by("user_key__username")


@transaction.atomic
def aprovar_vinculo(vinculo_id, ator):
    """
    Aprova um vínculo pendente. Exige que o ator seja administrador da instituição.
    """
    vinculo = _obter_vinculo(vinculo_id)

    _exigir_administrador(ator, vinculo.institution_key)

    if vinculo.status != Vinculo_instituicao.Status.PENDENTE:
        raise ValidationError("Somente vínculos pendentes podem ser aprovados.")

    vinculo.status = Vinculo_instituicao.Status.ATIVO
    vinculo.save(update_fields=["status"])

    return vinculo


@transaction.atomic
def recusar_vinculo(vinculo_id, ator):
    """
    Recusa um vínculo pendente. Exige que o ator seja administrador da instituição.
    """
    vinculo = _obter_vinculo(vinculo_id)

    _exigir_administrador(ator, vinculo.institution_key)

    if vinculo.status != Vinculo_instituicao.Status.PENDENTE:
        raise ValidationError("Somente vínculos pendentes podem ser recusados.")

    vinculo.status = Vinculo_instituicao.Status.RECUSADO
    vinculo.save(update_fields=["status"])

    return vinculo


@transaction.atomic
def remover_vinculo(vinculo_id, solicitante):
    """
    Remove um vínculo. O próprio usuário pode remover seu vínculo (desvincular-se).
    Para remover o vínculo de outro membro, é exigido cargo de administrador.
    Não permite a remoção do último administrador ativo da instituição.
    """
    vinculo = _obter_vinculo(vinculo_id)

    # O próprio usuário pode sair da instituição.
    # Para remover o vínculo de outra pessoa, precisa ser administrador.
    if vinculo.user_key_id != solicitante.id:
        _exigir_administrador(solicitante, vinculo.institution_key)

    # Impede a remoção do último administrador ativo
    if (
        vinculo.status == Vinculo_instituicao.Status.ATIVO
        and vinculo.cargo == Vinculo_instituicao.Cargo.ADMINISTRADOR
    ):
        quantidade_admins = Vinculo_instituicao.objects.filter(
            institution_key=vinculo.institution_key,
            status=Vinculo_instituicao.Status.ATIVO,
            cargo=Vinculo_instituicao.Cargo.ADMINISTRADOR,
        ).count()

        if quantidade_admins <= 1:
            raise ValidationError("Não é possível remover o último administrador ativo.")

    vinculo.delete()
    return True


@transaction.atomic
def alterar_cargo_membro(vinculo_id, novo_cargo, ator):
    """
    Altera o cargo de um membro ativo. Exige que o ator seja administrador da instituição.
    Impede que o último administrador ativo perca seu cargo.
    """
    vinculo = _obter_vinculo(vinculo_id)

    _exigir_administrador(ator, vinculo.institution_key)

    cargos_validos = [escolha[0] for escolha in Vinculo_instituicao.Cargo.choices]

    if novo_cargo not in cargos_validos:
        raise ValidationError("O cargo informado é inválido.")

    if vinculo.status != Vinculo_instituicao.Status.ATIVO:
        raise ValidationError("Só é possível alterar o cargo de um membro com vínculo ativo.")

    if (
        vinculo.cargo == Vinculo_instituicao.Cargo.ADMINISTRADOR
        and novo_cargo != Vinculo_instituicao.Cargo.ADMINISTRADOR
    ):
        quantidade_admins = Vinculo_instituicao.objects.filter(
            institution_key=vinculo.institution_key,
            status=Vinculo_instituicao.Status.ATIVO,
            cargo=Vinculo_instituicao.Cargo.ADMINISTRADOR,
        ).count()

        if quantidade_admins <= 1:
            raise ValidationError("Não é possível retirar o cargo do último administrador.")

    vinculo.cargo = novo_cargo
    vinculo.save(update_fields=["cargo"])

    return vinculo
