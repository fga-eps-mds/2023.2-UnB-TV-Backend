import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from src.utils.send_mail import send_verification_code

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

from src.main import app

client = TestClient(app)

class TestSendVerificationCode:
    @pytest.mark.asyncio
    @patch('src.utils.send_mail.fm.send_message', new_callable=AsyncMock)
    @patch('os.getenv', return_value='http://testurl.com')
    async def test_send_verification_code_success(self, mock_getenv, mock_send_message):
        email = "testuser@email.com"
        code = 123456
        is_unb = False

        response = await send_verification_code(email, code, is_unb)

        assert response.status_code == 200
        assert response.body.decode() == '{"status":"success"}'

        expected_html = f"<p>Seja bem-vindo ao UnB-TV! Para confirmar a criação da sua conta, utilize o código <strong>{code}</strong></p>"
        mock_send_message.assert_called_once_with(
            MessageSchema(
                subject="Confirme a criação da sua conta",
                recipients=[email],
                body=expected_html,
                subtype=MessageType.html
            )
        )

    @pytest.mark.asyncio
    @patch('src.utils.send_mail.fm.send_message', new_callable=AsyncMock)
    @patch('os.getenv', return_value='http://testurl.com')
    async def test_send_verification_code_is_unb(self, mock_getenv, mock_send_message):
        email = "testuser@unb.edu.br"
        code = 123456
        is_unb = True

        response = await send_verification_code(email, code, is_unb)

        assert response.status_code == 200
        assert response.body.decode() == '{"status":"success"}'

        expected_html = (f"<p>Seja bem-vindo ao UnB-TV! Para confirmar a criação da sua conta, utilize o código "
                         f"<strong>{code}</strong></p>"
                         f"<p>Como usuário da UnB, você pode configurar uma senha de administrador acessando o "
                         f"seguinte link após ativar sua conta: <a href='http://testurl.com/adminActivate?email={email}'>"
                         f"Configurar Senha de Administrador</a></p>")
        mock_send_message.assert_called_once_with(
            MessageSchema(
                subject="Confirme a criação da sua conta",
                recipients=[email],
                body=expected_html,
                subtype=MessageType.html
            )
        )