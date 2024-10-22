import sys
import os

# Adiciona o caminho do diretório 'src' ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pytest, os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from jose import JWTError
from fastapi import HTTPException

from src.main import app
from src.constants import errorMessages
from src.model import userModel
from src.utils import security, dotenv, send_mail, enumeration
from src.database import get_db, engine, Base
from src.repository import userRepository

valid_user_active_admin = {"name": "Forsen", "email": "valid@email.com", "connection": "PROFESSOR", "password": "123456"}
valid_user_active_user = {"name": "Guy Beahm", "email": "valid2@email.com", "connection": "ESTUDANTE", "password": "123456"}
duplicated_user = {"name": "John", "email": "valid@email.com", "connection": "ESTUDANTE", "password": "123456"} 
valid_user_not_active = {"name": "Peter", "email": "valid3@email.com", "connection": "ESTUDANTE", "password": "123456"}
valid_user_to_be_deleted = {"name": "Simon", "email": "valid4@email.com", "connection": "ESTUDANTE", "password": "123456"}
invalid_connection = {"name": "Mike", "email": "invalid@email.com", "connection": "INVALID", "password": "123456"}
invalid_pass_length = {"name": "Victor", "email": "invalid@email.com", "connection": "SERVIDOR", "password": "123"}
invalid_pass = {"name": "Luisa", "email": "invalid@email.com", "connection": "SERVIDOR", "password": "123abc"}
valid_social_user = { "name": "Paulo Kogos", "email": "kogos@email.com" }

total_registed_users = 5

client = TestClient(app)

class TestAuth:
    __admin_access_token__ = None
    __admin_refresh_token__ = None
    __user_access_token__ = None
    __user_refresh_token__ = None

    @pytest.fixture(scope="session", autouse=True)
    def setup(self, session_mocker):
        session_mocker.patch('utils.security.generate_six_digit_number_code', return_value=123456)
        session_mocker.patch('utils.send_mail.send_verification_code', return_value=JSONResponse(status_code=200, content={ "status": "success" }))
        session_mocker.patch('utils.send_mail.send_reset_password_code', return_value=JSONResponse(status_code=200, content={ "status": "success" }))

        # /register - ok
        response = client.post("/api/auth/register", json=valid_user_active_admin)
        data = response.json()
        assert response.status_code == 201
        assert data['status'] == 'success'

        response = client.post("/api/auth/register", json=valid_user_active_user)
        data = response.json()
        assert response.status_code == 201
        assert data['status'] == 'success'

        response = client.post("/api/auth/register", json=valid_user_not_active)
        data = response.json()
        assert response.status_code == 201
        assert data['status'] == 'success'

        response = client.post("/api/auth/register", json=valid_user_to_be_deleted)
        data = response.json()
        assert response.status_code == 201
        assert data['status'] == 'success'

        # /activate-account: ok 
        response = client.patch("/api/auth/activate-account", json={"email": valid_user_active_admin['email'], "code": 123456})
        data = response.json()
        assert response.status_code == 200
        assert data['status'] == 'success'

        response = client.patch("/api/auth/activate-account", json={"email": valid_user_active_user['email'], "code": 123456})
        data = response.json()
        assert response.status_code == 200
        assert data['status'] == 'success'

        # /login: ok
        response = client.post("/api/auth/login", json={"email": valid_user_active_admin['email'], "password": valid_user_active_admin['password']})
        data = response.json()
        assert response.status_code == 200
        assert data['token_type'] == 'bearer'
        assert security.verify_token(data['access_token'])['email'] == valid_user_active_admin['email']

        TestAuth.__admin_access_token__ = data['access_token']
        TestAuth.__admin_refresh_token__ = data['access_token']

        response = client.post("/api/auth/login", json={"email": valid_user_active_user['email'], "password": valid_user_active_user['password']})
        data = response.json()
        assert response.status_code == 200
        assert data['token_type'] == 'bearer'
        assert security.verify_token(data['access_token'])['email'] == valid_user_active_user['email']

        TestAuth.__user_access_token__ = data['access_token']
        TestAuth.__user_refresh_token__ = data['access_token']

        # login social - criação conta (nova)
        response = client.post('/api/auth/login/social', json=valid_social_user)
        data = response.json()
        assert response.status_code == 200
        assert data["access_token"] != None
        assert data["token_type"] == "bearer"
        assert data["is_new_user"] == True

        # Atualiza role do active_user_admin de USER para ADMIN
        with engine.connect() as connection:
            query = "UPDATE users SET role = 'ADMIN' WHERE id = 1;"
            connection.execute(text(query))
            connection.commit()

        yield

        userModel.Base.metadata.drop_all(bind=engine)

    def test_auth_get_connections(self, setup):
        response = client.get("/api/auth/vinculo")
        data = response.json()
        
        assert response.status_code == 200
        assert isinstance(data, list)
        assert len(data) == len(enumeration.UserConnection._value2member_map_)  

        for connection in enumeration.UserConnection:
            assert connection.value in data

    # REGISTER
    def test_auth_register_connection_invalid(self, setup):
        response = client.post("/api/auth/register", json=invalid_connection)
        data = response.json()
        assert response.status_code == 400
        assert data['detail'] == errorMessages.INVALID_CONNECTION

    def test_auth_register_password_invalid_length(self, setup):
        response = client.post("/api/auth/register", json=invalid_pass_length)
        data = response.json()
        assert response.status_code == 400
        assert data['detail'] == errorMessages.INVALID_PASSWORD

    def test_auth_register_password_invalid_characters(self, setup):
        response = client.post("/api/auth/register", json=invalid_pass)
        data = response.json()
        assert response.status_code == 400
        assert data['detail'] == errorMessages.INVALID_PASSWORD

    def test_auth_register_duplicate_email(self, setup):
        response = client.post("/api/auth/register", json=duplicated_user)
        data = response.json()
        assert response.status_code == 400
        assert data['detail'] == errorMessages.EMAIL_ALREADY_REGISTERED

    # LOGIN
    def test_auth_login_wrong_password(self, setup):
        response = client.post("/api/auth/login", json={ "email": valid_user_active_admin['email'], "password": "PASSWORD" })
        data = response.json()
        assert response.status_code == 404
        assert data['detail'] == errorMessages.PASSWORD_NO_MATCH

    def test_auth_login_not_found(self, setup):
        response = client.post("/api/auth/login", json=invalid_connection)
        data = response.json()
        assert response.status_code == 404
        assert data['detail'] == errorMessages.USER_NOT_FOUND

    def test_auth_login_not_active(self, setup):
        # /login - nao ativo
        response = client.post("/api/auth/login", json={"email": valid_user_not_active['email'], "password": valid_user_not_active['password']})
        data = response.json()
        assert response.status_code == 401
        assert data['detail'] == errorMessages.ACCOUNT_IS_NOT_ACTIVE

    def test_auth_login_social(self, setup):
        response = client.post('/api/auth/login/social', json=valid_social_user)
        data = response.json()
        assert response.status_code == 200
        assert data["access_token"] != None
        assert data["refresh_token"] != None
        assert data["token_type"] == "bearer"
        assert data["is_new_user"] == False

    # RESEND CODE
    def test_auth_resend_code_user_not_found(self, setup):
        response = client.post("/api/auth/resend-code", json={"email": invalid_connection['email']})
        data = response.json()
        assert response.status_code == 404
        assert data['detail'] == errorMessages.USER_NOT_FOUND

    def test_auth_resend_code_already_active(self, setup):
        response = client.post("/api/auth/resend-code", json={"email": valid_user_active_admin['email']})
        data = response.json()
        assert response.status_code == 400
        assert data['status'] == 'error'
        assert data['message'] == errorMessages.ACCOUNT_ALREADY_ACTIVE

    def test_auth_resend_code_success(self, setup):
        response = client.post("/api/auth/resend-code", json={"email": valid_user_not_active['email']})
        data = response.json()
        assert response.status_code == 201
        assert data['status'] == 'success'

    # ACTIVATE ACCOUNT
    def test_auth_activate_account_user_not_found(self, setup):
        response = client.patch("/api/auth/activate-account", json={"email": invalid_connection['email'], "code": 123456})
        data = response.json()
        assert response.status_code == 404

    def test_auth_activate_account_invalid_code(self, setup):
        # Garante que o código de ativação está correto
        response = client.patch("/api/auth/activate-account", json={"email": valid_user_not_active['email'], "code": 654321})
        data = response.json()
        assert response.status_code == 404
        assert data['detail'] == errorMessages.INVALID_CODE

    # ADMIN SETUP
    def test_admin_setup(self, setup):
        # Testa a tentativa com e-mail inválido
        response = client.post("/api/auth/admin-setup", json={"email": invalid_connection['email']})
        data = response.json()
        assert response.status_code == 404
        assert data['detail'] == errorMessages.USER_NOT_FOUND

        # Testa a tentativa com usuário inativo
        response = client.post("/api/auth/admin-setup", json={"email": valid_user_not_active['email']})
        data = response.json()
        assert response.status_code == 400
        assert data['detail'] == "Account is not active"

        # Testa a tentativa com e-mail que não contém "unb"
        response = client.post("/api/auth/admin-setup", json={"email": valid_user_active_user['email']})
        data = response.json()
        assert response.status_code == 400
        assert data['detail'] == "Account is not @unb"

    # SUPER ADMIN SETUP
    def test_admin_setup(self, setup):
        # Testa a tentativa com e-mail inválido
        response = client.post("/api/auth/super-admin-setup", json={"email": invalid_connection['email']})
        data = response.json()
        assert response.status_code == 404
        assert data['detail'] == errorMessages.USER_NOT_FOUND

        # Testa a tentativa com usuário inativo
        response = client.post("/api/auth/super-admin-setup", json={"email": valid_user_not_active['email']})
        data = response.json()
        assert response.status_code == 400
        assert data['detail'] == "Account is not active"

        # Testa a tentativa com e-mail que não contém "unb"
        response = client.post("/api/auth/super-admin-setup", json={"email": valid_user_active_user['email']})
        data = response.json()
        assert response.status_code == 400
        assert data['detail'] == "Account is not @unb"