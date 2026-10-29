from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from accounts import service


def responder_erro(erro, status_code=status.HTTP_400_BAD_REQUEST):
    if hasattr(erro, "message_dict"):
        mensagem = erro.message_dict
    elif hasattr(erro, "messages"):
        mensagem = erro.messages if len(erro.messages) > 1 else erro.messages[0]
    else:
        mensagem = str(erro)

    return Response({"erro": mensagem}, status=status_code)


def serializar_usuario(usuario):
    return {
        "id": usuario.id,
        "username": usuario.username,
        "email": usuario.email,
        "description": usuario.description,
    }


def serializar_instituicao(instituicao):
    return {
        "id": instituicao.id,
        "name": instituicao.name,
        "slug": instituicao.slug,
        "site": instituicao.site,
        "description": instituicao.description,
        "location": instituicao.location,
        "verificada": instituicao.verificada,
        "data_entrada": str(instituicao.data_entrada),
    }


def serializar_vinculo(vinculo):
    return {
        "id": vinculo.id,
        "usuario": {
            "id": vinculo.user_key.id,
            "username": vinculo.user_key.username,
            "email": vinculo.user_key.email,
        },
        "instituicao": {
            "id": vinculo.institution_key.id,
            "name": vinculo.institution_key.name,
            "slug": vinculo.institution_key.slug,
        },
        "cargo": vinculo.cargo,
        "status": vinculo.status,
        "email_instituicao": vinculo.email_instituicao,
        "data_vinculo": str(vinculo.data_vinculo),
    }


# ==============================
# AUTENTICAÇÃO E SESSÃO
# ==============================

@api_view(["POST"])
@permission_classes([AllowAny])
def cadastrar_usuario_view(request):
    """
    Cadastro de novos usuários. Bloqueia qualquer atribuição de privilégios administrativos.
    """
    dados = request.data or {}

    campos_admin = {"is_staff", "is_superuser"}
    if any(dados.get(campo) for campo in campos_admin):
        return Response(
            {"erro": "Usuários comuns não podem definir privilégios administrativos."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        usuario = service.cadastrar_usuario(
            username=dados.get("username", ""),
            email=dados.get("email", ""),
            password=dados.get("password", ""),
            description=dados.get("description", ""),
        )

        return Response(
            {
                "mensagem": "Usuário cadastrado com sucesso.",
                "usuario": serializar_usuario(usuario),
            },
            status=status.HTTP_201_CREATED,
        )

    except PermissionDenied as erro:
        return responder_erro(erro, status.HTTP_403_FORBIDDEN)
    except ValidationError as erro:
        return responder_erro(erro, status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login do Athenis aceitando username ou email, junto com a senha.
    Retorna os dados do usuário e o par de tokens JWT (access e refresh).
    """
    dados = request.data or {}
    identificador = (
        dados.get("username")
        or dados.get("email")
        or dados.get("identificador")
        or ""
    )
    password = dados.get("password", "")

    try:
        usuario, tokens = service.login_usuario(
            identificador=identificador,
            password=password,
        )

        return Response(
            {
                "mensagem": "Login realizado com sucesso.",
                "tokens": tokens,
                "usuario": serializar_usuario(usuario),
            },
            status=status.HTTP_200_OK,
        )

    except PermissionDenied as erro:
        return responder_erro(erro, status.HTTP_403_FORBIDDEN)
    except ValidationError as erro:
        return responder_erro(erro, status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def renovar_token_view(request):
    """
    Renovação do token de acesso JWT utilizando o refresh token.
    """
    dados = request.data or {}
    refresh_token = dados.get("refresh", "")

    try:
        resultado = service.renovar_token_acesso(refresh_token)
        return Response(resultado, status=status.HTTP_200_OK)

    except ValidationError as erro:
        return responder_erro(erro, status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout do usuário através da revogação do refresh token (blacklist).
    """
    dados = request.data or {}
    refresh_token = dados.get("refresh", "")

    try:
        service.revogar_token(refresh_token)
        return Response(
            {"mensagem": "Logout realizado com sucesso."},
            status=status.HTTP_200_OK,
        )

    except ValidationError as erro:
        return responder_erro(erro, status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def usuario_logado_view(request):
    """
    Retorna os dados do usuário autenticado atual.
    """
    return Response(serializar_usuario(request.user), status=status.HTTP_200_OK)


# ==============================
# PERFIL E USUÁRIOS
# ==============================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def buscar_usuario_view(request, user_id):
    usuario = service.buscar_usuario(user_id)

    if usuario is None:
        return Response(
            {"erro": "Usuário não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(serializar_usuario(usuario), status=status.HTTP_200_OK)


@api_view(["PATCH", "PUT"])
@permission_classes([IsAuthenticated])
def atualizar_perfil_view(request, user_id):
    dados = request.data or {}

    try:
        usuario = service.atualizar_perfil(
            user_id=user_id,
            username=dados.get("username"),
            email=dados.get("email"),
            description=dados.get("description"),
            solicitante=request.user,
            dados_extras=dados,
        )

        return Response(
            {
                "mensagem": "Perfil atualizado com sucesso.",
                "usuario": serializar_usuario(usuario),
            },
            status=status.HTTP_200_OK,
        )

    except PermissionDenied as erro:
        return responder_erro(erro, status.HTTP_403_FORBIDDEN)
    except ValidationError as erro:
        return responder_erro(erro, status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def desativar_conta_view(request, user_id):
    try:
        usuario = service.desativar_conta(user_id, solicitante=request.user)

        return Response(
            {
                "mensagem": "Conta desativada com sucesso.",
                "usuario_id": usuario.id,
            },
            status=status.HTTP_200_OK,
        )

    except PermissionDenied as erro:
        return responder_erro(erro, status.HTTP_403_FORBIDDEN)
    except ValidationError as erro:
        return responder_erro(erro, status.HTTP_400_BAD_REQUEST)


# ==============================
# INSTITUIÇÕES
# ==============================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cadastrar_instituicao_view(request):
    dados = request.data or {}

    try:
        instituicao = service.cadastrar_instituicao(
            name=dados.get("name", ""),
            site=dados.get("site", ""),
            description=dados.get("description", ""),
            location=dados.get("location", ""),
            criador=request.user,
        )

        return Response(
            {
                "mensagem": "Instituição cadastrada com sucesso.",
                "instituicao": serializar_instituicao(instituicao),
            },
            status=status.HTTP_201_CREATED,
        )

    except ValidationError as erro:
        return responder_erro(erro, status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([AllowAny])
def listar_instituicoes_view(request):
    instituicoes = service.listar_instituicoes()
    resultados = [serializar_instituicao(inst) for inst in instituicoes]
    return Response({"instituicoes": resultados}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def buscar_instituicao_view(request, institution_id):
    try:
        instituicao = service.buscar_instituicao(institution_id)
        return Response(serializar_instituicao(instituicao), status=status.HTTP_200_OK)
    except ValidationError as erro:
        return responder_erro(erro, status.HTTP_404_NOT_FOUND)


# ==============================
# VÍNCULOS INSTITUCIONAIS
# ==============================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def solicitar_vinculo_view(request, institution_id=None):
    """
    Solicita vínculo institucional utilizando com segurança o usuário autenticado da requisição.
    """
    dados = request.data or {}
    inst_id = institution_id or dados.get("institution_id")

    if not inst_id:
        return Response(
            {"erro": "O ID da instituição é obrigatório."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        instituicao = service.buscar_instituicao(inst_id)
        email_instituicao = dados.get("email_instituicao", "")

        vinculo = service.solicitar_vinculo(
            user=request.user,
            institution=instituicao,
            email_instituicao=email_instituicao,
        )

        return Response(
            {
                "mensagem": "Solicitação de vínculo realizada com sucesso.",
                "vinculo": serializar_vinculo(vinculo),
            },
            status=status.HTTP_201_CREATED,
        )

    except PermissionDenied as erro:
        return responder_erro(erro, status.HTTP_403_FORBIDDEN)
    except ValidationError as erro:
        return responder_erro(erro, status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def listar_meus_vinculos_view(request):
    """
    Lista todos os vínculos do usuário autenticado.
    Suporta filtro por query param `status` (PENDENTE, ATIVO, RECUSADO).
    """
    status_filtro = request.query_params.get("status")
    vinculos = service.listar_vinculos_usuario(request.user, status=status_filtro)
    return Response(
        {"vinculos": [serializar_vinculo(v) for v in vinculos]},
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def listar_membros_instituicao_view(request, institution_id):
    """
    Lista membros de uma instituição.
    Filtro `status` (padrão ATIVO). Vínculos PENDENTES ou RECUSADOS exigem cargo de administrador.
    """
    try:
        instituicao = service.buscar_instituicao(institution_id)
        status_filtro = request.query_params.get("status", "ATIVO")

        membros = service.listar_membros_instituicao(
            institution=instituicao,
            status=status_filtro,
            solicitante=request.user,
        )

        return Response(
            {"membros": [serializar_vinculo(m) for m in membros]},
            status=status.HTTP_200_OK,
        )

    except PermissionDenied as erro:
        return responder_erro(erro, status.HTTP_403_FORBIDDEN)
    except ValidationError as erro:
        return responder_erro(erro, status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def aprovar_vinculo_view(request, vinculo_id):
    """
    Aprova uma solicitação de vínculo. Exige que o solicitante seja administrador da instituição.
    """
    try:
        vinculo = service.aprovar_vinculo(vinculo_id, ator=request.user)
        return Response(
            {
                "mensagem": "Vínculo aprovado com sucesso.",
                "vinculo": serializar_vinculo(vinculo),
            },
            status=status.HTTP_200_OK,
        )

    except PermissionDenied as erro:
        return responder_erro(erro, status.HTTP_403_FORBIDDEN)
    except ValidationError as erro:
        return responder_erro(erro, status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def recusar_vinculo_view(request, vinculo_id):
    """
    Recusa uma solicitação de vínculo. Exige que o solicitante seja administrador da instituição.
    """
    try:
        vinculo = service.recusar_vinculo(vinculo_id, ator=request.user)
        return Response(
            {
                "mensagem": "Vínculo recusado com sucesso.",
                "vinculo": serializar_vinculo(vinculo),
            },
            status=status.HTTP_200_OK,
        )

    except PermissionDenied as erro:
        return responder_erro(erro, status.HTTP_403_FORBIDDEN)
    except ValidationError as erro:
        return responder_erro(erro, status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE", "POST"])
@permission_classes([IsAuthenticated])
def remover_vinculo_view(request, vinculo_id):
    """
    Remove um vínculo existente (desvinculação ou exclusão por administrador).
    """
    try:
        service.remover_vinculo(vinculo_id, solicitante=request.user)
        return Response(
            {"mensagem": "Vínculo removido com sucesso."},
            status=status.HTTP_200_OK,
        )

    except PermissionDenied as erro:
        return responder_erro(erro, status.HTTP_403_FORBIDDEN)
    except ValidationError as erro:
        return responder_erro(erro, status.HTTP_400_BAD_REQUEST)


@api_view(["PATCH", "POST"])
@permission_classes([IsAuthenticated])
def alterar_cargo_membro_view(request, vinculo_id):
    """
    Altera o cargo de um membro ativo na instituição. Exige privilégios de administrador.
    """
    dados = request.data or {}
    novo_cargo = dados.get("cargo")

    if not novo_cargo:
        return Response(
            {"erro": "O novo cargo deve ser informado."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        vinculo = service.alterar_cargo_membro(
            vinculo_id=vinculo_id,
            novo_cargo=novo_cargo,
            ator=request.user,
        )

        return Response(
            {
                "mensagem": "Cargo atualizado com sucesso.",
                "vinculo": serializar_vinculo(vinculo),
            },
            status=status.HTTP_200_OK,
        )

    except PermissionDenied as erro:
        return responder_erro(erro, status.HTTP_403_FORBIDDEN)
    except ValidationError as erro:
        return responder_erro(erro, status.HTTP_400_BAD_REQUEST)
