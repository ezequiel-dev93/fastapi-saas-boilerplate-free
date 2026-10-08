# Skill: new-module

## Description
Create a new business module following the project's Screaming Architecture conventions. Generates the complete module structure with models, schemas, services, routes, and registers it in the main app.

## Usage
```
/new-module <module_name> [--with-gateway] [--with-dependencies]
```

## Examples
```
/new-module products
/new-module notifications --with-gateway
/new-module analytics --with-dependencies
```

## Implementation Steps

### 1. Validate Input
- Module name must be lowercase, snake_case (e.g., `products`, `user_settings`)
- Check if module already exists in `api/modules/`

### 2. Create Directory Structure
```
api/modules/<module_name>/
├── __init__.py
├── models.py
├── schemas.py
├── services.py
├── routes.py
├── dependencies.py    # Only if --with-dependencies
└── gateway.py         # Only if --with-gateway
```

### 3. Generate Files from Templates

#### models.py
```python
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, Boolean
from datetime import datetime
from api.core.database import Base

class <PascalCaseName>(Base):
    __tablename__ = "<module_name>"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="<module_name>")
```

#### schemas.py
```python
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

class <PascalCaseName>Base(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class <PascalCaseName>Create(<PascalCaseName>Base):
    pass

class <PascalCaseName>Update(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class <PascalCaseName>Response(<PascalCaseName>Base):
    model_config = ConfigDict(from_attributes=True)
    id: int
    organization_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

#### services.py
```python
from sqlalchemy.orm import Session
from typing import Optional, List
from api.modules.<module_name>.models import <PascalCaseName>
from api.modules.<module_name>.schemas import <PascalCaseName>Create, <PascalCaseName>Update

class <PascalCaseName>Service:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: <PascalCaseName>Create, organization_id: int) -> <PascalCaseName>:
        entity = <PascalCaseName>(**data.model_dump(), organization_id=organization_id)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, entity_id: int, organization_id: int) -> Optional[<PascalCaseName>]:
        return self.db.query(<PascalCaseName>).filter(
            <PascalCaseName>.id == entity_id,
            <PascalCaseName>.organization_id == organization_id
        ).first()

    def list_all(self, organization_id: int, skip: int = 0, limit: int = 100) -> List[<PascalCaseName>]:
        return self.db.query(<PascalCaseName>).filter(
            <PascalCaseName>.organization_id == organization_id
        ).offset(skip).limit(limit).all()

    def update(self, entity_id: int, organization_id: int, data: <PascalCaseName>Update) -> Optional[<PascalCaseName>]:
        entity = self.get_by_id(entity_id, organization_id)
        if not entity:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(entity, field, value)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity_id: int, organization_id: int) -> bool:
        entity = self.get_by_id(entity_id, organization_id)
        if not entity:
            return False
        self.db.delete(entity)
        self.db.commit()
        return True
```

#### routes.py
```python
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List
from api.core.database import get_db
from api.core.security import get_current_user
from api.modules.organizations.dependencies import get_active_organization, require_org_role
from api.modules.users.models import UserProfile
from api.modules.organizations.models import Organization, OrganizationMember
from .schemas import <PascalCaseName>Create, <PascalCaseName>Update, <PascalCaseName>Response
from .services import <PascalCaseName>Service

router = APIRouter(prefix="/<module_name>", tags=["<PascalCaseName>"])

@router.post("", response_model=<PascalCaseName>Response, status_code=status.HTTP_201_CREATED)
def create_<module_name>(
    data: <PascalCaseName>Create,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
):
    service = <PascalCaseName>Service(db)
    return service.create(data, org.id)

@router.get("", response_model=List[<PascalCaseName>Response])
def list_<module_name>s(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
):
    service = <PascalCaseName>Service(db)
    return service.list_all(org.id, skip, limit)

@router.get("/{entity_id}", response_model=<PascalCaseName>Response)
def get_<module_name>(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
):
    service = <PascalCaseName>Service(db)
    entity = service.get_by_id(entity_id, org.id)
    if not entity:
        raise HTTPException(status_code=404, detail="<PascalCaseName> not found")
    return entity

@router.patch("/{entity_id}", response_model=<PascalCaseName>Response)
def update_<module_name>(
    entity_id: int,
    data: <PascalCaseName>Update,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    membership: OrganizationMember = Depends(require_org_role(["owner", "admin"])),
):
    service = <PascalCaseName>Service(db)
    entity = service.update(entity_id, org.id, data)
    if not entity:
        raise HTTPException(status_code=404, detail="<PascalCaseName> not found")
    return entity

@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_<module_name>(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    membership: OrganizationMember = Depends(require_org_role(["owner"])),
):
    service = <PascalCaseName>Service(db)
    if not service.delete(entity_id, org.id):
        raise HTTPException(status_code=404, detail="<PascalCaseName> not found")
```

#### dependencies.py (if --with-dependencies)
```python
from typing import Callable, List
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_user
from api.modules.organizations.dependencies import get_current_org_membership
from api.modules.organizations.models import OrganizationMember
from api.modules.<module_name>.models import <PascalCaseName>

def require_<module_name>_access(allowed_roles: List[str] = ["owner", "admin", "member"]) -> Callable:
    """Dependency to check access to a specific <module_name> entity."""
    async def checker(
        entity_id: int,
        membership: OrganizationMember = Depends(get_current_org_membership),
        db: Session = Depends(get_db),
    ) -> <PascalCaseName>:
        entity = db.query(<PascalCaseName>).filter(
            <PascalCaseName>.id == entity_id,
            <PascalCaseName>.organization_id == membership.organization_id
        ).first()
        if not entity:
            raise HTTPException(status_code=404, detail="<PascalCaseName> not found")
        if membership.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return entity
    return checker
```

#### gateway.py (if --with-gateway)
```python
from typing import Protocol
from api.modules.<module_name>.schemas import <PascalCaseName>Create, <PascalCaseName>Response

class <PascalCaseName>GatewayProtocol(Protocol):
    """Protocol for external <module_name> integrations."""
    
    async def create_external(self, data: <PascalCaseName>Create) -> <PascalCaseName>Response: ...
    async def sync_from_external(self, external_id: str) -> <PascalCaseName>Response: ...


class Dummy<PascalCaseName>Gateway:
    """Fake implementation for testing."""
    
    async def create_external(self, data: <PascalCaseName>Create) -> <PascalCaseName>Response:
        return <PascalCaseName>Response(
            id=0,
            name=data.name,
            description=data.description,
            organization_id=0,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def sync_from_external(self, external_id: str) -> <PascalCaseName>Response:
        raise NotImplementedError("Dummy gateway")
```

### 4. Register in Main App
Add to `api/main.py`:
```python
from api.modules.<module_name> import routes as <module_name>_routes
app.include_router(<module_name>_routes.router)
```

### 5. Create Alembic Migration
```bash
alembic revision --autogenerate -m "add <module_name> module"
```

### 6. Run Tests to Verify
```bash
pytest tests/modules/<module_name>/ -v
```

## Notes
- Always use `organization_id` for multi-tenancy isolation
- Follow the existing code style (type hints, async where needed)
- Services should be testable with mocked DB session
- Routes stay thin - all logic in services