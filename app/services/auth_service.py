import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import abort, current_app, request
from flask_login import current_user
from app.database import db
from app.models import User
from app.extensions import bcrypt
from app.services.audit_service import AuditService

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.generate_password_hash(password).decode('utf-8')

    @staticmethod
    def check_password(password_hash: str, password: str) -> bool:
        return bcrypt.check_password_hash(password_hash, password)

    @staticmethod
    def register_user(email: str, password: str, role: str) -> User:
        """Register a user with a hashed password."""
        hashed = AuthService.hash_password(password)
        user = User(email=email, password_hash=hashed, role=role)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def authenticate_user(email: str, password: str) -> User:
        """
        Authenticate user credentials.
        Returns the user object if successful, None otherwise.
        """
        user = User.query.filter_by(email=email).first()
        if user and AuthService.check_password(user.password_hash, password):
            if user.is_active:
                return user
        return None

    @staticmethod
    def generate_jwt_token(user: User) -> str:
        """Generate a JWT token for stateless REST API interactions."""
        payload = {
            'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
            'iat': datetime.utcnow(),
            'sub': user.id,
            'role': user.role,
            'email': user.email
        }
        return jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )

    @staticmethod
    def decode_jwt_token(token: str) -> dict:
        """Decode a JWT token and return the payload."""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            return {'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'error': 'Invalid token'}


def role_required(roles):
    """
    Decorator for views that checks if the logged-in user has the required role.
    roles can be a single string or a list of strings.
    """
    if isinstance(roles, str):
        roles = [roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # Unauthorized
            if current_user.role not in roles:
                # Log unauthorized access attempt
                AuditService.log_event(
                    action="unauthorized_access_attempt",
                    user_id=current_user.id,
                    email=current_user.email,
                    details=f"User attempted to access role-restricted route. Required: {roles}, actual: {current_user.role}"
                )
                abort(403)  # Forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def api_jwt_required(roles=None):
    """
    Decorator for REST API endpoints checking for JWT header authorization.
    """
    if roles and isinstance(roles, str):
        roles = [roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return {'message': 'Missing or invalid Authorization header'}, 401
                
            token = auth_header.split(" ")[1]
            payload = AuthService.decode_jwt_token(token)
            
            if 'error' in payload:
                return {'message': payload['error']}, 401
                
            # If role checks are required
            if roles and payload.get('role') not in roles:
                return {'message': 'Access forbidden: Insufficient permissions'}, 403
                
            # Pass the token payload to kwargs so route handlers can read user info if needed
            kwargs['jwt_payload'] = payload
            return f(*args, **kwargs)
        return decorated_function
    return decorator
