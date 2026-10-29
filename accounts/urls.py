from django.urls import path
from accounts import views

urlpatterns = [
    # ==============================
    # AUTENTICAÇÃO E SESSÃO JWT
    # ==============================
    path(
        "auth/cadastro/",
        views.cadastrar_usuario_view,
        name="auth_cadastro",
    ),
    path(
        "auth/login/",
        views.login_view,
        name="auth_login",
    ),
    path(
        "auth/refresh/",
        views.renovar_token_view,
        name="auth_refresh",
    ),
    path(
        "auth/logout/",
        views.logout_view,
        name="auth_logout",
    ),
    path(
        "auth/me/",
        views.usuario_logado_view,
        name="auth_me",
    ),

    # ==============================
    # USUÁRIOS
    # ==============================
    path(
        "usuarios/",
        views.cadastrar_usuario_view,
        name="cadastrar_usuario",
    ),
    path(
        "usuarios/<int:user_id>/",
        views.buscar_usuario_view,
        name="buscar_usuario",
    ),
    path(
        "usuarios/<int:user_id>/perfil/",
        views.atualizar_perfil_view,
        name="atualizar_perfil",
    ),
    path(
        "usuarios/<int:user_id>/desativar/",
        views.desativar_conta_view,
        name="desativar_conta",
    ),

    # ==============================
    # INSTITUIÇÕES
    # ==============================
    path(
        "instituicoes/",
        views.cadastrar_instituicao_view,
        name="cadastrar_instituicao",
    ),
    path(
        "instituicoes/listar/",
        views.listar_instituicoes_view,
        name="listar_instituicoes",
    ),
    path(
        "instituicoes/<int:institution_id>/",
        views.buscar_instituicao_view,
        name="buscar_instituicao",
    ),
    path(
        "instituicoes/<int:institution_id>/solicitar/",
        views.solicitar_vinculo_view,
        name="solicitar_vinculo_instituicao",
    ),
    path(
        "instituicoes/<int:institution_id>/membros/",
        views.listar_membros_instituicao_view,
        name="listar_membros_instituicao",
    ),

    # ==============================
    # VÍNCULOS INSTITUCIONAIS
    # ==============================
    path(
        "vinculos/",
        views.solicitar_vinculo_view,
        name="solicitar_vinculo",
    ),
    path(
        "vinculos/meus/",
        views.listar_meus_vinculos_view,
        name="listar_meus_vinculos",
    ),
    path(
        "vinculos/<int:vinculo_id>/",
        views.remover_vinculo_view,
        name="remover_vinculo_delete",
    ),
    path(
        "vinculos/<int:vinculo_id>/aprovar/",
        views.aprovar_vinculo_view,
        name="aprovar_vinculo",
    ),
    path(
        "vinculos/<int:vinculo_id>/recusar/",
        views.recusar_vinculo_view,
        name="recusar_vinculo",
    ),
    path(
        "vinculos/<int:vinculo_id>/remover/",
        views.remover_vinculo_view,
        name="remover_vinculo",
    ),
    path(
        "vinculos/<int:vinculo_id>/cargo/",
        views.alterar_cargo_membro_view,
        name="alterar_cargo_membro",
    ),
]
