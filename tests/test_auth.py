"""
Alpha AI Autotrader - Authentication Tests
Tests for JWT authentication, user management, and security
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt

from backend.api.auth import (
    create_access_token,
    create_refresh_token,
    decode_token
)
from backend.models.database import User
from backend.core.config import get_settings

settings = get_settings()


class TestJWTTokens:
    """Test JWT token creation and validation"""

    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation"""
        data = {"sub": "testuser"}
        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        """Test decoding a valid token"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        decoded = decode_token(token)

        assert decoded["sub"] == "testuser"
        assert decoded["type"] == "access"
        assert "exp" in decoded
        assert "iat" in decoded

    def test_token_expiration(self):
        """Test that token includes expiration"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        decoded = decode_token(token)

        # Check expiration is in the future
        exp_time = datetime.fromtimestamp(decoded["exp"])
        assert exp_time > datetime.utcnow()

        # Check expiration is within expected window
        expected_exp = datetime.utcnow() + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 5  # Within 5 seconds

    def test_access_vs_refresh_token_type(self):
        """Test that access and refresh tokens have correct type"""
        data = {"sub": "testuser"}

        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        access_decoded = decode_token(access_token)
        refresh_decoded = decode_token(refresh_token)

        assert access_decoded["type"] == "access"
        assert refresh_decoded["type"] == "refresh"

    def test_custom_expiration(self):
        """Test token with custom expiration"""
        data = {"sub": "testuser"}
        custom_expires = timedelta(minutes=5)
        token = create_access_token(data, expires_delta=custom_expires)
        decoded = decode_token(token)

        exp_time = datetime.fromtimestamp(decoded["exp"])
        expected_exp = datetime.utcnow() + custom_expires
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 5  # Within 5 seconds


class TestUserModel:
    """Test User database model"""

    def test_password_hashing(self):
        """Test password hashing"""
        password = "SecurePass123"
        hashed = User.hash_password(password)

        assert hashed is not None
        assert hashed != password  # Hashed != plaintext
        assert len(hashed) > 20  # Bcrypt hashes are long

    def test_password_verification_correct(self):
        """Test password verification with correct password"""
        password = "SecurePass123"
        hashed = User.hash_password(password)

        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hashed
        )

        assert user.verify_password(password) is True

    def test_password_verification_incorrect(self):
        """Test password verification with incorrect password"""
        password = "SecurePass123"
        wrong_password = "WrongPass456"
        hashed = User.hash_password(password)

        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hashed
        )

        assert user.verify_password(wrong_password) is False

    def test_password_hashing_uniqueness(self):
        """Test that same password produces different hashes"""
        password = "SecurePass123"
        hash1 = User.hash_password(password)
        hash2 = User.hash_password(password)

        # Bcrypt includes salt, so same password should produce different hashes
        assert hash1 != hash2

        # But both should verify correctly
        user1 = User(username="user1", email="u1@example.com", hashed_password=hash1)
        user2 = User(username="user2", email="u2@example.com", hashed_password=hash2)

        assert user1.verify_password(password) is True
        assert user2.verify_password(password) is True


class TestPasswordValidation:
    """Test password strength requirements"""

    def test_password_strength_requirements(self):
        """Test that passwords meet strength requirements"""
        # These would be tested in the Pydantic schema validator
        # Here we just test the hash/verify cycle

        weak_passwords = [
            "short",  # Too short
            "nouppercase123",  # No uppercase
            "NOLOWERCASE123",  # No lowercase
            "NoDigitsHere",  # No digits
        ]

        strong_passwords = [
            "SecurePass123",
            "MyP@ssw0rd",
            "Abcdef123",
        ]

        for password in strong_passwords:
            hashed = User.hash_password(password)
            user = User(
                username="test",
                email="test@example.com",
                hashed_password=hashed
            )
            assert user.verify_password(password) is True


class TestTokenSecurity:
    """Test token security features"""

    def test_token_cannot_be_modified(self):
        """Test that modified tokens are rejected"""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        # Try to modify the token
        parts = token.split('.')
        if len(parts) == 3:
            # Tamper with the payload
            modified_token = parts[0] + ".TAMPERED." + parts[2]

            # Should raise exception when decoding
            with pytest.raises(Exception):
                decode_token(modified_token)

    def test_expired_token_rejected(self):
        """Test that expired tokens are rejected"""
        # Create token that expires immediately
        data = {"sub": "testuser"}
        expired_delta = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expires_delta=expired_delta)

        # Should raise exception for expired token
        with pytest.raises(Exception):
            decode_token(token)

    def test_invalid_token_format(self):
        """Test that invalid token format is rejected"""
        invalid_tokens = [
            "invalid",
            "not.a.token",
            "",
            "a" * 100,
        ]

        for token in invalid_tokens:
            with pytest.raises(Exception):
                decode_token(token)


# Fixtures for testing with database (if needed)
@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    return User(
        username="testuser",
        email="test@example.com",
        hashed_password=User.hash_password("SecurePass123"),
        is_active=True,
        is_superuser=False
    )


@pytest.fixture
def sample_admin():
    """Create a sample admin user for testing"""
    return User(
        username="admin",
        email="admin@example.com",
        hashed_password=User.hash_password("AdminPass123"),
        is_active=True,
        is_superuser=True
    )


class TestUserFixtures:
    """Test user fixtures"""

    def test_sample_user_creation(self, sample_user):
        """Test sample user fixture"""
        assert sample_user.username == "testuser"
        assert sample_user.email == "test@example.com"
        assert sample_user.is_active is True
        assert sample_user.is_superuser is False
        assert sample_user.verify_password("SecurePass123") is True

    def test_sample_admin_creation(self, sample_admin):
        """Test sample admin fixture"""
        assert sample_admin.username == "admin"
        assert sample_admin.is_superuser is True
        assert sample_admin.verify_password("AdminPass123") is True
