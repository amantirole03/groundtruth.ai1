import pytest
from fastapi import HTTPException
from app.api.v1.endpoints.auth import register, login
from app.schemas.schemas import UserRegister, UserLogin
from app.core.security import decode_access_token

def test_register_and_login_success(db_session):
    email = "newuser@groundtruth.ai"
    password = "ValidPassword123!"

    # Registration
    reg_out = register(UserRegister(email=email, password=password), db=db_session)
    assert reg_out["access_token"] is not None
    assert reg_out["user"].email == email

    # Verify JWT Token
    payload = decode_access_token(reg_out["access_token"])
    assert payload is not None
    assert payload["sub"] == reg_out["user"].id

    # Login
    login_out = login(UserLogin(email=email, password=password), db=db_session)
    assert login_out["access_token"] is not None
    assert login_out["user"].email == email

def test_register_duplicate_email(db_session):
    email = "duplicate@groundtruth.ai"
    password = "Password123!"

    register(UserRegister(email=email, password=password), db=db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        register(UserRegister(email=email, password=password), db=db_session)
    assert exc_info.value.status_code == 400
    assert "already exists" in exc_info.value.detail

def test_login_invalid_password(db_session, test_user_1):
    with pytest.raises(HTTPException) as exc_info:
        login(UserLogin(email=test_user_1.email, password="WrongPassword!"), db=db_session)
    assert exc_info.value.status_code == 401
    assert "Incorrect email or password" in exc_info.value.detail

def test_login_nonexistent_user(db_session):
    with pytest.raises(HTTPException) as exc_info:
        login(UserLogin(email="ghost@groundtruth.ai", password="AnyPassword123!"), db=db_session)
    assert exc_info.value.status_code == 401
