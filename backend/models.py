from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False)

class User(Base, TimestampMixin):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

class Organization(Base, TimestampMixin):
    __tablename__ = 'organizations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    users = relationship("User", backref="organization")

class Project(Base, TimestampMixin):
    __tablename__ = 'projects'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    users = relationship("User", backref="project")

class Agent(Base, TimestampMixin):
    __tablename__ = 'agents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    type = Column(String(50), nullable=False)

class Task(Base, TimestampMixin):
    __tablename__ = 'tasks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id'), nullable=False)
    status = Column(String(50), nullable=False)

class Execution(Base, TimestampMixin):
    __tablename__ = 'executions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)

class Memory(Base, TimestampMixin):
    __tablename__ = 'memory'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey('executions.id'), nullable=False)
    data = Column(Text, nullable=False)

class Sandbox(Base, TimestampMixin):
    __tablename__ = 'sandboxes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    container_id = Column(String(100), unique=True, nullable=False)

class Integration(Base, TimestampMixin):
    __tablename__ = 'integrations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    service_name = Column(String(100), nullable=False)
    config = Column(Text, nullable=False)

class AuditLog(Base, TimestampMixin):
    __tablename__ = 'audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)

# Indexes for common queries
Index('idx_user_username', User.username)
Index('idx_organization_name', Organization.name)
Index('idx_project_name', Project.name)
Index('idx_agent_name', Agent.name)
Index('idx_task_name', Task.name)
Index('idx_execution_start_time', Execution.start_time)
Index('idx_sandbox_container_id', Sandbox.container_id)
Index('idx_integration_service_name', Integration.service_name)
Index('idx_auditlog_action', AuditLog.action)
