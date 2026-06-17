import logging
from flask import request
from app.database import db
from app.models import AuditLog

# Set up logging to stdout
logger = logging.getLogger("student_platform_audit")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[AUDIT] %(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class AuditService:
    @staticmethod
    def log_event(action: str, details: str = None, user_id: int = None, email: str = None, ip_address: str = None) -> AuditLog:
        """
        Record a system or security event in the database and structured application logs.
        """
        # Resolve client IP if not provided
        if not ip_address:
            # Check for proxy header (behind AWS Application Load Balancer)
            if request:
                ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            else:
                ip_address = '127.0.0.1'
                
        # Handle cases where user_id or email can be derived from current context
        # But we pass them explicitly for precision
        
        # Save to Database
        try:
            log_entry = AuditLog(
                user_id=user_id,
                email=email,
                action=action,
                details=details,
                ip_address=ip_address
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to write audit log to database: {e}")
            log_entry = None
            
        # Write to system logs (parsed by CloudWatch Agent)
        log_msg = f"Action: {action} | User: {user_id or email or 'System'} | IP: {ip_address} | Details: {details or 'N/A'}"
        logger.info(log_msg)
        
        return log_entry
