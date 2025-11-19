# Authentication & Security Guide

## Overview

Alpha AI Autotrader now has a complete JWT-based authentication system for securing API endpoints and WebSocket connections.

## Features

### ✅ Implemented

- **JWT Authentication** - Token-based authentication using JSON Web Tokens
- **User Management** - User registration, login, profile updates
- **Password Security** - Bcrypt hashing with strong password requirements
- **Account Protection** - Failed login lockout (5 attempts = 30 min lock)
- **CORS Configuration** - Environment-based origin whitelisting
- **Token Refresh** - Long-lived refresh tokens for seamless re-authentication
- **Role-Based Access** - Superuser/admin permissions
- **API Key Auth** - Optional server-to-server authentication

### 🔒 Security Features

1. **Password Requirements**:
   - Minimum 8 characters
   - At least 1 uppercase letter
   - At least 1 lowercase letter
   - At least 1 digit
   - Hashed with bcrypt

2. **Account Lockout**:
   - 5 failed login attempts = 30-minute lockout
   - Automatic reset on successful login

3. **Token Expiration**:
   - Access tokens: 30 minutes (default)
   - Refresh tokens: 7 days (default)

4. **CORS Protection**:
   - Whitelist-based origin validation
   - Configurable via environment variables

---

## Setup

### 1. Configure Environment Variables

Add to your `.env` file:

```env
# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,https://yourdomain.com

# JWT Authentication
# CRITICAL: Generate a strong secret key!
# Run: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your-super-secret-key-change-this
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Optional API Key Authentication
REQUIRE_API_KEY=false
API_KEYS=key1,key2,key3
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:
- `python-jose[cryptography]` - JWT token handling
- `passlib[bcrypt]` - Password hashing
- `email-validator` - Email validation

### 3. Initialize Database

The User table will be created automatically on first run:

```bash
python3 backend/api/main.py
```

### 4. Create Admin User

Run the interactive admin user creation script:

```bash
python3 create_admin_user.py
```

Example:
```
Enter admin username (default: admin): admin
Enter admin email: admin@example.com
Enter full name (optional): Admin User
Enter password (min 8 chars): ********
Confirm password: ********

✅ Admin user created successfully!
```

---

## API Endpoints

### Authentication Routes

All auth routes are under `/api/auth/`:

#### POST `/api/auth/register`
Register a new user account

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-15T10:00:00"
}
```

#### POST `/api/auth/login`
Login with username/email and password

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "SecurePass123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "is_active": true
  }
}
```

#### POST `/api/auth/refresh`
Refresh access token using refresh token

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### GET `/api/auth/me`
Get current user information (requires authentication)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "last_login": "2025-01-15T10:00:00"
}
```

#### PUT `/api/auth/me`
Update current user information

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "full_name": "John Doe Jr.",
  "password": "NewSecurePass123"
}
```

#### POST `/api/auth/change-password`
Change user password

**Request Body:**
```json
{
  "current_password": "SecurePass123",
  "new_password": "NewSecurePass456"
}
```

#### GET `/api/auth/users` (Admin Only)
List all users (requires superuser)

**Query Parameters:**
- `skip` - Number of records to skip (pagination)
- `limit` - Maximum records to return (default: 100)

#### DELETE `/api/auth/users/{user_id}` (Admin Only)
Delete a user (requires superuser)

---

## Usage Examples

### JavaScript/TypeScript (Frontend)

```javascript
// 1. Login
async function login(username, password) {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });

  const data = await response.json();

  // Store tokens
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);

  return data.user;
}

// 2. Make authenticated request
async function getProfile() {
  const token = localStorage.getItem('access_token');

  const response = await fetch('http://localhost:8000/api/auth/me', {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  return response.json();
}

// 3. Refresh token when expired
async function refreshToken() {
  const refresh = localStorage.getItem('refresh_token');

  const response = await fetch('http://localhost:8000/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh })
  });

  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
}

// 4. WebSocket with authentication
const ws = new WebSocket('ws://localhost:8000/ws');
const token = localStorage.getItem('access_token');

ws.onopen = () => {
  // Send authentication message
  ws.send(JSON.stringify({
    type: 'authenticate',
    token: token
  }));
};
```

### Python

```python
import requests

# 1. Login
response = requests.post('http://localhost:8000/api/auth/login', json={
    'username': 'admin',
    'password': 'SecurePass123'
})
tokens = response.json()

access_token = tokens['access_token']
refresh_token = tokens['refresh_token']

# 2. Make authenticated request
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get('http://localhost:8000/api/auth/me', headers=headers)
user = response.json()

print(f"Logged in as: {user['username']}")
```

### cURL

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"SecurePass123"}'

# Get profile (replace TOKEN with actual token)
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer TOKEN"
```

---

## Protecting Your Endpoints

### Option 1: Require Authentication

```python
from fastapi import APIRouter, Depends
from backend.api.auth import get_current_user
from backend.models.database import User

router = APIRouter()

@router.get("/protected-endpoint")
async def protected_route(current_user: User = Depends(get_current_user)):
    """This endpoint requires authentication"""
    return {"message": f"Hello {current_user.username}!"}
```

### Option 2: Require Admin/Superuser

```python
from backend.api.auth import get_current_superuser

@router.delete("/admin-only")
async def admin_route(current_user: User = Depends(get_current_superuser)):
    """Only superusers can access this"""
    return {"message": "Admin access granted"}
```

### Option 3: Optional Authentication

```python
from backend.api.auth import get_optional_user

@router.get("/optional-auth")
async def optional_route(current_user: User = Depends(get_optional_user)):
    """Works with or without authentication"""
    if current_user:
        return {"message": f"Hello {current_user.username}!"}
    return {"message": "Hello guest!"}
```

### Option 4: API Key Authentication

```python
from backend.api.auth import verify_api_key

@router.post("/webhook")
async def webhook(api_key_valid: bool = Depends(verify_api_key)):
    """Requires API key in X-API-Key header"""
    return {"message": "Webhook received"}
```

---

## WebSocket Authentication

To protect WebSocket connections, update the WebSocket handler in `backend/api/main.py`:

```python
from .auth import decode_token

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Wait for authentication message
    try:
        auth_data = await websocket.receive_json()

        if auth_data.get("type") != "authenticate":
            await websocket.close(code=1008, reason="Authentication required")
            return

        # Verify token
        token = auth_data.get("token")
        payload = decode_token(token)
        username = payload.get("sub")

        # User is authenticated, proceed...

    except Exception as e:
        await websocket.close(code=1008, reason="Authentication failed")
        return
```

---

## Production Checklist

### 🔒 Security

- [ ] Change `JWT_SECRET_KEY` to a strong random value
- [ ] Set `CORS_ALLOWED_ORIGINS` to your actual domain(s)
- [ ] Enable HTTPS (SSL/TLS certificates)
- [ ] Set `DEBUG=false`
- [ ] Use strong passwords for admin accounts
- [ ] Regularly rotate JWT secret keys
- [ ] Implement rate limiting (see HIGH priority tasks)
- [ ] Monitor failed login attempts

### 📊 Monitoring

- [ ] Log all authentication attempts
- [ ] Set up alerts for:
  - Multiple failed logins
  - Account lockouts
  - Unusual access patterns
- [ ] Track token usage and expiration

### 🧪 Testing

- [ ] Test login/logout flows
- [ ] Test token refresh mechanism
- [ ] Test account lockout after failed attempts
- [ ] Test password strength validation
- [ ] Test CORS configuration with real frontend

---

## Troubleshooting

### Error: "Not authenticated"
- Token is missing or malformed
- Check `Authorization: Bearer <token>` header

### Error: "Invalid authentication credentials"
- Token is expired or invalid
- Refresh token using `/api/auth/refresh`

### Error: "Account is temporarily locked"
- Too many failed login attempts
- Wait 30 minutes or contact admin

### Error: "CORS policy blocked"
- Add your frontend origin to `CORS_ALLOWED_ORIGINS`
- Example: `CORS_ALLOWED_ORIGINS=http://localhost:3000,https://app.example.com`

---

## Next Steps

1. ✅ CORS configuration
2. ✅ JWT authentication
3. 🔄 Input validation (next task)
4. 🔄 Rate limiting
5. 🔄 Exception handling improvements

For more details, see `COMPREHENSIVE_CODE_REVIEW.md`.
