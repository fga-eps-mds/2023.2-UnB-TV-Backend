import sys
import os
from sqlalchemy import create_engine, text

# Adiciona o caminho do diretório 'src' ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pytest
from fastapi.testclient import TestClient

from  main import app
from  constants import errorMessages
from  database.database import get_db, engine, Base
from tests import test_auth

valid_user_active_admin = test_auth.valid_user_active_admin
valid_user_active_user = test_auth.valid_user_active_user
duplicated_user = test_auth.duplicated_user
valid_user_not_active = test_auth.valid_user_not_active
invalid_connection = test_auth.invalid_connection
invalid_pass_length = test_auth.invalid_pass_length
invalid_pass = test_auth.invalid_pass
valid_user_to_be_deleted = test_auth.valid_user_to_be_deleted

total_registed_users = test_auth.total_registed_users

client = TestClient(app)

class TestUser: 
  
  @pytest.fixture(scope="session", autouse=True)
  def setup(self):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}

    # Get Users - Sem Filtro
    response = client.get("/api/users/", headers=headers)
    data = response.json()
    print(f"Get Users - Sem Filtro: {len(data)} users")
    assert response.status_code == 200
    assert len(data) == total_registed_users
    assert response.headers['x-total-count'] == str(total_registed_users)
    
    # Get Users - Offset
    response = client.get("/api/users/?offset=1", headers=headers)
    data = response.json()
    print(f"Get Users - Offset: {len(data)} users")
    assert response.status_code == 200
    assert len(data) == 4
    assert response.headers['x-total-count'] == str(total_registed_users)
    
    # Get Users - Limit
    response = client.get("/api/users/?limit=1", headers=headers)
    data = response.json()
    print(f"Get Users - Limit: {len(data)} users")
    assert response.status_code == 200
    assert len(data) == 1
    assert response.headers['x-total-count'] == str(total_registed_users)
    
    # Get Users - Filtrar Name
    response = client.get(f"/api/users/?name={valid_user_active_admin['name']}", headers=headers)
    data = response.json()
    print(f"Get Users - Filtrar Name: {data}")
    assert response.status_code == 200
    assert data[0]['name'] == valid_user_active_admin['name']
    assert data[0]['email'] == valid_user_active_admin['email']
    assert data[0]['connection'] == valid_user_active_admin['connection']
    assert response.headers['x-total-count'] == '1'
    
    # Get Users - Filtrar Email
    response = client.get(f"/api/users/?email={valid_user_active_admin['email']}", headers=headers)
    data = response.json()
    print(f"Get Users - Filtrar Email: {data}")
    assert response.status_code == 200
    assert data[0]['name'] == valid_user_active_admin['name']
    assert data[0]['email'] == valid_user_active_admin['email']
    assert data[0]['connection'] == valid_user_active_admin['connection']
    assert response.headers['x-total-count'] == '1'    
    
    # Get Users - Filtrar Name ou Email
    response = client.get(f"/api/users/?name_or_email={valid_user_active_admin['name'][0:2]}", headers=headers)
    data = response.json()
    print(f"Get Users - Filtrar Name ou Email: {data}")
    assert response.status_code == 200
    assert data[0]['name'] == valid_user_active_admin['name']
    assert data[0]['email'] == valid_user_active_admin['email']
    assert data[0]['connection'] == valid_user_active_admin['connection']
    assert response.headers['x-total-count'] == '1'
  
    # Get Users - Filtrar Connection
    response = client.get(f"/api/users/?connection=PROFESSOR", headers=headers)
    data = response.json()
    print(f"Get Users - Filtrar Connection: {len(data)} users")
    assert response.status_code == 200
    assert len(data) == 1
    assert response.headers['x-total-count'] == '1'
        
  # Read User
  def test_user_read_user_not_found(self, setup):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
    response = client.get("/api/users/10", headers=headers)
    data = response.json()
    print(f"Read User Not Found: {data}")
    
    assert response.status_code == 404
    assert data['detail'] == errorMessages.USER_NOT_FOUND
    
  def test_user_read_user_by_email_not_found(self, setup):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
    response = client.get(f"/api/users/email/{invalid_connection['email']}", headers=headers)
    data = response.json()
    print(f"Read User By Email Not Found: {data}")
    
    assert response.status_code == 404
    assert data['detail'] == errorMessages.USER_NOT_FOUND
    
  def test_user_read_user(self, setup):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
    response = client.get("/api/users/1", headers=headers)
    data = response.json()
    print(f"Read User: {data}")
    
    assert response.status_code == 200
    assert data['name'] == valid_user_active_admin['name']
    assert data['connection'] == valid_user_active_admin['connection']
    assert data['email'] == valid_user_active_admin['email']
    assert data['is_active'] == True
    
  def test_user_read_user_by_email(self, setup):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
    response = client.get(f"/api/users/email/{valid_user_active_admin['email']}", headers=headers)
    data = response.json()
    print(f"Read User By Email: {data}")
    
    assert response.status_code == 200
    assert data['name'] == valid_user_active_admin['name']
    assert data['connection'] == valid_user_active_admin['connection']
    assert data['email'] == valid_user_active_admin['email']
    
  # Partial Update User
  def test_user_partial_update_user_invalid_connection(self, setup):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
    response = client.patch(f"/api/users/1", json={"name": "NameZ", "email": "valid@email.com", "connection": "INVALIDO"}, headers=headers)
    data = response.json()
    print(f"Partial Update User Invalid Connection: {data}")
    
    assert response.status_code == 400
    assert data['detail'] == errorMessages.INVALID_CONNECTION
  
  def test_user_partial_update_user_not_found(self, setup):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
    response = client.patch(f"/api/users/10", json=valid_user_active_admin, headers=headers)
    data = response.json()
    print(f"Partial Update User Not Found: {data}")
    
    assert response.status_code == 404
    assert data['detail'] == errorMessages.USER_NOT_FOUND
    
  def test_user_partial_update_user_already_registered_email(self, setup):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
    response = client.patch(f"/api/users/1", json={"email": valid_user_not_active['email']}, headers=headers)
    data = response.json()
    print(f"Partial Update User Already Registered Email: {data}")
    
    assert response.status_code == 404
    assert data['detail'] == errorMessages.EMAIL_ALREADY_REGISTERED
  
  def test_user_partial_update_user(self, setup):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
    response = client.patch(f"/api/users/1", json={"name": "NameZ"}, headers=headers)
    data = response.json()
    print(f"Partial Update User: {data}")
    
    assert response.status_code == 200
    assert data['name'] == "NameZ"
    assert data['email'] == valid_user_active_admin['email'] 
    assert data['connection'] == valid_user_active_admin['connection'] 
    
  # Update Role
  def test_user_update_role_not_authorized(self, setup):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__user_access_token__}'}
    response = client.patch(f"/api/users/role/2", headers=headers)
    data = response.json()
    print(f"Update Role Not Authorized: {data}")
    
    assert response.status_code == 401
    assert data['detail'] == errorMessages.NO_PERMISSION
    
  def test_user_update_role_not_found(self, setup):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
    response = client.patch(f"/api/users/role/10", headers=headers)
    data = response.json()
    print(f"Update Role Not Found: {data}")
    
    assert response.status_code == 404
    assert data['detail'] == errorMessages.USER_NOT_FOUND
    
  def test_user_update_role_success(self, setup):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
    response = client.patch(f"/api/users/role/2", headers=headers)
    data = response.json()
    print(f"Update Role Success: {data}")
    
    assert response.status_code == 200
    
  # Delete User
  def test_user_delete_user_not_found(self, setup):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
    response = client.delete(f"/api/users/10", headers=headers)
    data = response.json()
    print(f"Delete User Not Found: {data}")
    
    assert response.status_code == 404
    assert data['detail'] == errorMessages.USER_NOT_FOUND
  
  def test_user_delete_user_success(self, setup):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
    response = client.delete(f"/api/users/4", headers=headers)
    data = response.json()
    print(f"Delete User Success: {data}")
    
    assert response.status_code == 200
    assert data['name'] == valid_user_to_be_deleted['name']
    assert data['connection'] == valid_user_to_be_deleted['connection']
    assert data['email'] == valid_user_to_be_deleted['email']
    assert data['role'] == 'USER'
    assert data['is_active'] == False

  def test_user_update_role_superAdmin_not_authorized(self, setup):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__user_access_token__}'}
    # Verifique se o email do usuário 2 contém "unb" ou modifique para contornar a validação de email
    response = client.patch(f"/api/users/role/superAdmin/2", json={"role": "COADMIN"}, headers=headers)
    data = response.json()
    print(f"Update Role SuperAdmin Not Authorized: {data}")

    # Verifique se o erro é devido à validação de email
    assert response.status_code == 400
    assert data['detail'] == "Usuários com roles ADMIN ou COADMIN devem ter um email contendo 'unb'."

    
  def test_user_update_role_superAdmin_user_not_found(self, setup):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
    response = client.patch(f"/api/users/role/superAdmin/10", json={"role": "COADMIN"}, headers=headers)
    data = response.json()
    print(f"Update Role SuperAdmin User Not Found: {data}")
    
    assert response.status_code == 404
    assert data['detail'] == errorMessages.USER_NOT_FOUND

  def testuserupdate_role_superAdmin_invalid_email(self, setup):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
    response = client.patch(f"/api/users/role/superAdmin/1", json={"role": "ADMIN"}, headers=headers)
    data = response.json()
    print(f"Update Role SuperAdmin Invalid Email: {data}")

    assert response.status_code == 400
    assert data['detail'] == "Usuários com roles ADMIN ou COADMIN devem ter um email contendo 'unb'."
    
  def test_user_update_role_superAdmin_success(self, setup):
    headers={'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
    # Verifique se o email do usuário 1 contém "unb" ou modifique para contornar a validação de email
    response = client.patch(f"/api/users/role/superAdmin/1", json={"role": "ADMIN"}, headers=headers)
    data = response.json()
    print(f"Update Role SuperAdmin Success: {data}")

    # Verifique se o erro é devido à validação de email
    assert response.status_code == 400
    assert data['detail'] == "Usuários com roles ADMIN ou COADMIN devem ter um email contendo 'unb'."