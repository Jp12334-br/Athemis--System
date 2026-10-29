from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts import service
from accounts.models import Institution, Vinculo_instituicao

User = get_user_model()


class AccountsServiceTests(TestCase):
    def setUp(self):
        self.user1 = service.cadastrar_usuario(
            username="joao",
            email="joao@athenis.org",
            password="SenhaForte123!",
            description="Pesquisador no Athenis",
        )
        self.user2 = service.cadastrar_usuario(
            username="maria",
            email="maria@athenis.org",
            password="OutraSenha123!",
            description="Cientista de dados",
        )

    def test_cadastrar_usuario_sucesso(self):
        usuario = service.cadastrar_usuario(
            username="pedro",
            email="pedro@athenis.org",
            password="Senha123!",
        )
        self.assertEqual(usuario.username, "pedro")
        self.assertEqual(usuario.email, "pedro@athenis.org")
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)

    def test_cadastrar_usuario_validacoes(self):
        # Email duplicado
        with self.assertRaises(ValidationError):
            service.cadastrar_usuario("outro", "joao@athenis.org", "Senha123!")

        # Username duplicado
        with self.assertRaises(ValidationError):
            service.cadastrar_usuario("joao", "novo@athenis.org", "Senha123!")

        # Email inválido
        with self.assertRaises(ValidationError):
            service.cadastrar_usuario("teste", "email_invalido", "Senha123!")

    def test_autenticar_usuario_por_username_e_email(self):
        # Login por username
        u1 = service.autenticar_usuario("joao", "SenhaForte123!")
        self.assertEqual(u1.id, self.user1.id)

        # Login por email
        u2 = service.autenticar_usuario("joao@athenis.org", "SenhaForte123!")
        self.assertEqual(u2.id, self.user1.id)

        # Senha incorreta
        with self.assertRaises(ValidationError):
            service.autenticar_usuario("joao", "senha_errada")

        # Usuário inexistente
        with self.assertRaises(ValidationError):
            service.autenticar_usuario("inexistente", "Senha123!")

    def test_autenticar_usuario_desativado(self):
        service.desativar_conta(self.user1.id, solicitante=self.user1)
        with self.assertRaises(ValidationError):
            service.autenticar_usuario("joao", "SenhaForte123!")

    def test_tokens_jwt_e_renovacao(self):
        tokens = service.gerar_tokens_para_usuario(self.user1)
        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)

        # Renovação de token
        novo_token = service.renovar_token_acesso(tokens["refresh"])
        self.assertIn("access", novo_token)

        # Logout / revogação do token
        revogado = service.revogar_token(tokens["refresh"])
        self.assertTrue(revogado)

        # Tentativa de renovar com token revogado deve falhar
        with self.assertRaises(ValidationError):
            service.renovar_token_acesso(tokens["refresh"])

    def test_atualizar_perfil_proprio_usuario(self):
        usuario = service.atualizar_perfil(
            user_id=self.user1.id,
            description="Nova descrição",
            solicitante=self.user1,
        )
        self.assertEqual(usuario.description, "Nova descrição")

    def test_atualizar_perfil_bloqueia_outro_usuario(self):
        # user2 tenta alterar o perfil de user1
        with self.assertRaises(PermissionDenied):
            service.atualizar_perfil(
                user_id=self.user1.id,
                description="Hacked",
                solicitante=self.user2,
            )

    def test_atualizar_perfil_bloqueia_privilegios_admin(self):
        with self.assertRaises(PermissionDenied):
            service.atualizar_perfil(
                user_id=self.user1.id,
                solicitante=self.user1,
                dados_extras={"is_staff": True},
            )

    def test_desativar_conta_permissao(self):
        # user2 tenta desativar user1
        with self.assertRaises(PermissionDenied):
            service.desativar_conta(self.user1.id, solicitante=self.user2)

        # user1 desativa sua própria conta
        usuario = service.desativar_conta(self.user1.id, solicitante=self.user1)
        self.assertFalse(usuario.is_active)

    def test_instituicao_e_vinculos_workflow_completo(self):
        # 1. user1 cria a instituição e vira admin ativo
        inst = service.cadastrar_instituicao(
            name="Instituto Athenis",
            site="https://athenis.org",
            description="Instituto de Ciência Aberta",
            criador=self.user1,
        )
        self.assertEqual(inst.name, "Instituto Athenis")
        self.assertTrue(
            Vinculo_instituicao.objects.filter(
                user_key=self.user1,
                institution_key=inst,
                cargo=Vinculo_instituicao.Cargo.ADMINISTRADOR,
                status=Vinculo_instituicao.Status.ATIVO,
            ).exists()
        )

        # 2. user2 solicita vínculo
        vinculo_maria = service.solicitar_vinculo(
            user=self.user2,
            institution=inst,
            email_instituicao="maria@athenis.org",
        )
        self.assertEqual(vinculo_maria.status, Vinculo_instituicao.Status.PENDENTE)
        self.assertEqual(vinculo_maria.cargo, Vinculo_instituicao.Cargo.MEMBRO)

        # 3. user2 (não admin) tenta aprovar seu próprio vínculo -> falha
        with self.assertRaises(PermissionDenied):
            service.aprovar_vinculo(vinculo_maria.id, ator=self.user2)

        # 4. user1 (admin) aprova o vínculo
        vinculo_aprovado = service.aprovar_vinculo(vinculo_maria.id, ator=self.user1)
        self.assertEqual(vinculo_aprovado.status, Vinculo_instituicao.Status.ATIVO)

        # 5. user1 altera o cargo de user2 para PESQUISADOR
        vinculo_atualizado = service.alterar_cargo_membro(
            vinculo_id=vinculo_aprovado.id,
            novo_cargo=Vinculo_instituicao.Cargo.PESQUISADOR,
            ator=self.user1,
        )
        self.assertEqual(vinculo_atualizado.cargo, Vinculo_instituicao.Cargo.PESQUISADOR)

        # 6. user1 tenta retirar o próprio cargo de administrador (sendo o único admin) -> deve falhar
        vinculo_admin = Vinculo_instituicao.objects.get(
            user_key=self.user1, institution_key=inst
        )
        with self.assertRaises(ValidationError):
            service.alterar_cargo_membro(
                vinculo_id=vinculo_admin.id,
                novo_cargo=Vinculo_instituicao.Cargo.MEMBRO,
                ator=self.user1,
            )

        # 7. user2 remove seu próprio vínculo
        removido = service.remover_vinculo(vinculo_maria.id, solicitante=self.user2)
        self.assertTrue(removido)
        self.assertFalse(Vinculo_instituicao.objects.filter(id=vinculo_maria.id).exists())


class AccountsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = service.cadastrar_usuario(
            username="carlos",
            email="carlos@athenis.org",
            password="SenhaForte123!",
        )
        self.other_user = service.cadastrar_usuario(
            username="ana",
            email="ana@athenis.org",
            password="SenhaForte123!",
        )

        tokens = service.gerar_tokens_para_usuario(self.user)
        self.access_token = tokens["access"]
        self.refresh_token = tokens["refresh"]

    def test_api_cadastro_usuario(self):
        response = self.client.post(
            "/api/usuarios/",
            {
                "username": "novo_usuario",
                "email": "novo@athenis.org",
                "password": "SenhaSegura123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["usuario"]["username"], "novo_usuario")

    def test_api_cadastro_usuario_bloqueia_privilegios_admin(self):
        response = self.client.post(
            "/api/usuarios/",
            {
                "username": "hacker",
                "email": "hacker@athenis.org",
                "password": "SenhaSegura123!",
                "is_staff": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_login_com_username(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "carlos",
                "password": "SenhaForte123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])

    def test_api_login_com_email(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "carlos@athenis.org",
                "password": "SenhaForte123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", response.data)
        self.assertEqual(response.data["usuario"]["username"], "carlos")

    def test_api_login_credenciais_invalidas(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "carlos",
                "password": "senha_incorreta",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_renovar_token(self):
        response = self.client.post(
            "/api/auth/refresh/",
            {"refresh": self.refresh_token},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_api_logout_e_blacklist(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(
            "/api/auth/logout/",
            {"refresh": self.refresh_token},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Tentativa de renovação com o token colocado na blacklist
        self.client.credentials()
        response_refresh = self.client.post(
            "/api/auth/refresh/",
            {"refresh": self.refresh_token},
            format="json",
        )
        self.assertEqual(response_refresh.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_protecao_rotas_sem_token(self):
        # Acesso sem token
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Acesso com token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response_auth = self.client.get("/api/auth/me/")
        self.assertEqual(response_auth.status_code, status.HTTP_200_OK)
        self.assertEqual(response_auth.data["username"], "carlos")

    def test_api_atualizar_perfil_apenas_proprio_usuario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # Atualizar próprio perfil
        response = self.client.patch(
            f"/api/usuarios/{self.user.id}/perfil/",
            {"description": "Minha biografia atualizada"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Tentar atualizar perfil de outro usuário
        response_outro = self.client.patch(
            f"/api/usuarios/{self.other_user.id}/perfil/",
            {"description": "Tentativa indevida"},
            format="json",
        )
        self.assertEqual(response_outro.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_atualizar_perfil_bloqueia_privilegios_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.patch(
            f"/api/usuarios/{self.user.id}/perfil/",
            {"is_staff": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_workflow_instituicoes_e_vinculos(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # 1. Carlos cria instituição
        resp_inst = self.client.post(
            "/api/instituicoes/",
            {
                "name": "Laboratório de IA",
                "site": "https://ia.athenis.org",
                "description": "Pesquisas em inteligência artificial",
                "location": "São Paulo",
            },
            format="json",
        )
        self.assertEqual(resp_inst.status_code, status.HTTP_201_CREATED)
        inst_id = resp_inst.data["instituicao"]["id"]

        # 2. Ana se autentica e solicita vínculo
        tokens_ana = service.gerar_tokens_para_usuario(self.other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens_ana['access']}")

        resp_vinc = self.client.post(
            "/api/vinculos/",
            {
                "institution_id": inst_id,
                "email_instituicao": "ana@ia.athenis.org",
            },
            format="json",
        )
        self.assertEqual(resp_vinc.status_code, status.HTTP_201_CREATED)
        vinculo_id = resp_vinc.data["vinculo"]["id"]

        # 3. Ana tenta aprovar o próprio vínculo -> deve receber 403
        resp_aprov_ana = self.client.post(f"/api/vinculos/{vinculo_id}/aprovar/")
        self.assertEqual(resp_aprov_ana.status_code, status.HTTP_403_FORBIDDEN)

        # 4. Carlos (admin) aprova o vínculo de Ana
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        resp_aprov_carlos = self.client.post(f"/api/vinculos/{vinculo_id}/aprovar/")
        self.assertEqual(resp_aprov_carlos.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_aprov_carlos.data["vinculo"]["status"], "ATIVO")

        # 5. Carlos altera o cargo de Ana para PESQUISADOR
        resp_cargo = self.client.patch(
            f"/api/vinculos/{vinculo_id}/cargo/",
            {"cargo": "PESQUISADOR"},
            format="json",
        )
        self.assertEqual(resp_cargo.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_cargo.data["vinculo"]["cargo"], "PESQUISADOR")

        # 6. Ana visualiza seus próprios vínculos
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens_ana['access']}")
        resp_meus_vinculos = self.client.get("/api/vinculos/meus/")
        self.assertEqual(resp_meus_vinculos.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_meus_vinculos.data["vinculos"]), 1)

        # 7. Ana remove seu próprio vínculo (desvinculação)
        resp_remover = self.client.delete(f"/api/vinculos/{vinculo_id}/")
        self.assertEqual(resp_remover.status_code, status.HTTP_200_OK)
