# Skill: generate-tests

## Description
Generate comprehensive test scaffolding for a module including unit tests, integration tests, fixtures, and mocks following the project's testing patterns.

## Usage
```
/generate-tests <module_name> [--type=unit|integration|all] [--coverage=high]
```

## Examples
```
/generate-tests products --type=all
/generate-tests analytics --type=unit --coverage=high
/generate-tests billing --type=integration
```

## Test Structure
```
tests/
├── conftest.py                 # Shared fixtures
├── modules/
│   ├── <module_name>/
│   │   ├── test_models.py      # ORM model tests
│   │   ├── test_schemas.py     # Pydantic validation tests
│   │   ├── test_services.py    # Business logic tests (unit)
│   │   ├── test_routes.py      # HTTP endpoint tests (integration)
│   │   └── test_dependencies.py # RBAC/feature gating tests
├── test_auth.py                # Dual auth tests
├── test_billing_webhooks.py    # Stripe webhook tests
└── test_organizations_rbac.py  # Multi-tenancy tests
```

## Generated Test Templates

### 1. conftest.py Fixtures (Module-Specific)
```python
# tests/modules/<module_name>/conftest.py
import pytest
from sqlalchemy.orm import Session
from api.modules.<module_name>.models import <PascalCaseName>
from api.modules.organizations.models import Organization
from api.modules.users.models import UserProfile

@pytest.fixture
def sample_<module_name>(db: Session, org: Organization) -> <PascalCaseName>:
    """Create a sample entity for testing."""
    entity = <PascalCaseName>(
        name="Test <PascalCaseName>",
        description="Test description",
        organization_id=org.id,
        is_active=True
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity

@pytest.fixture
def <module_name>_data() -> dict:
    """Valid create data for <PascalCaseName>."""
    return {
        "name": "New <PascalCaseName>",
        "description": "New description"
    }

@pytest.fixture
def <module_name>_update_data() -> dict:
    """Valid update data for <PascalCaseName>."""
    return {
        "name": "Updated <PascalCaseName>",
        "is_active": False
    }
```

### 2. test_models.py
```python
# tests/modules/<module_name>/test_models.py
import pytest
from sqlalchemy.orm import Session
from api.modules.<module_name>.models import <PascalCaseName>
from api.modules.organizations.models import Organization

class Test<PascalCaseName>Model:
    def test_create_<module_name>(self, db: Session, org: Organization):
        entity = <PascalCaseName>(
            name="Test",
            organization_id=org.id
        )
        db.add(entity)
        db.commit()
        
        assert entity.id is not None
        assert entity.name == "Test"
        assert entity.organization_id == org.id
        assert entity.is_active is True  # default
        assert entity.created_at is not None

    def test_organization_relationship(self, db: Session, org: Organization, sample_<module_name>):
        # Test back_populates works
        db.refresh(org)
        assert sample_<module_name> in org.<module_name>s

    def test_organization_isolation(self, db: Session, org: Organization, other_org: Organization):
        """Ensure entities are scoped to organization."""
        entity1 = <PascalCaseName>(name="Org1", organization_id=org.id)
        entity2 = <PascalCaseName>(name="Org2", organization_id=other_org.id)
        db.add_all([entity1, entity2])
        db.commit()
        
        org1_entities = db.query(<PascalCaseName>).filter(
            <PascalCaseName>.organization_id == org.id
        ).all()
        assert len(org1_entities) == 1
        assert org1_entities[0].name == "Org1"
```

### 3. test_schemas.py
```python
# tests/modules/<module_name>/test_schemas.py
import pytest
from pydantic import ValidationError
from api.modules.<module_name>.schemas import (
    <PascalCaseName>Create, 
    <PascalCaseName>Update, 
    <PascalCaseName>Response
)

class Test<PascalCaseName>Schemas:
    def test_create_valid(self, <module_name>_data):
        schema = <PascalCaseName>Create(**<module_name>_data)
        assert schema.name == <module_name>_data["name"]
        assert schema.description == <module_name>_data["description"]

    def test_create_invalid_empty_name(self):
        with pytest.raises(ValidationError) as exc:
            <PascalCaseName>Create(name="")
        assert "String should have at least 1 character" in str(exc.value)

    def test_create_invalid_long_name(self):
        with pytest.raises(ValidationError) as exc:
            <PascalCaseName>Create(name="x" * 101)
        assert "String should have at most 100 characters" in str(exc.value)

    def test_update_partial(self, <module_name>_update_data):
        schema = <PascalCaseName>Update(**<module_name>_update_data)
        assert schema.name == "Updated <PascalCaseName>"
        assert schema.is_active is False

    def test_response_from_orm(self, sample_<module_name>):
        response = <PascalCaseName>Response.model_validate(sample_<module_name>)
        assert response.id == sample_<module_name>.id
        assert response.name == sample_<module_name>.name
```

### 4. test_services.py (Unit Tests with Mocked DB)
```python
# tests/modules/<module_name>/test_services.py
import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session
from api.modules.<module_name>.services import <PascalCaseName>Service
from api.modules.<module_name>.schemas import <PascalCaseName>Create, <PascalCaseName>Update
from api.modules.<module_name>.models import <PascalCaseName>
from api.modules.organizations.models import Organization

class Test<PascalCaseName>Service:
    @pytest.fixture
    def service(self):
        return <PascalCaseName>Service(db=Mock(spec=Session))

    @pytest.fixture
    def mock_db(self, service):
        return service.db

    def test_create(self, service, mock_db, <module_name>_data):
        # Setup
        created_entity = <PascalCaseName>(id=1, **<module_name>_data, organization_id=1)
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock(side_effect=lambda x: setattr(x, 'id', 1))

        # Execute
        result = service.create(<PascalCaseName>Create(**<module_name>_data), organization_id=1)

        # Assert
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert result.name == <module_name>_data["name"]
        assert result.organization_id == 1

    def test_get_by_id_found(self, service, mock_db):
        entity = <PascalCaseName>(id=1, name="Test", organization_id=1)
        mock_db.query.return_value.filter.return_value.first.return_value = entity

        result = service.get_by_id(1, organization_id=1)

        assert result == entity
        mock_db.query.assert_called_with(<PascalCaseName>)

    def test_get_by_id_not_found(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_by_id(999, organization_id=1)

        assert result is None

    def test_list_all(self, service, mock_db):
        entities = [
            <PascalCaseName>(id=1, name="A", organization_id=1),
            <PascalCaseName>(id=2, name="B", organization_id=1),
        ]
        mock_query = Mock()
        mock_query.filter.return_value.offset.return_value.limit.return_value.all.return_value = entities
        mock_db.query.return_value = mock_query

        result = service.list_all(organization_id=1, skip=0, limit=100)

        assert len(result) == 2
        mock_query.filter.assert_called()

    def test_update(self, service, mock_db):
        existing = <PascalCaseName>(id=1, name="Old", organization_id=1)
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        result = service.update(1, 1, <PascalCaseName>Update(name="New"))

        assert result.name == "New"
        mock_db.commit.assert_called_once()

    def test_delete(self, service, mock_db):
        existing = <PascalCaseName>(id=1, name="Test", organization_id=1)
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        result = service.delete(1, 1)

        assert result is True
        mock_db.delete.assert_called_with(existing)
        mock_db.commit.assert_called_once()
```

### 5. test_routes.py (Integration Tests)
```python
# tests/modules/<module_name>/test_routes.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from api.modules.<module_name>.models import <PascalCaseName>
from api.modules.organizations.models import Organization, OrganizationMember
from api.modules.users.models import UserProfile

class Test<PascalCaseName>Routes:
    def test_create_<module_name>_success(self, client: TestClient, auth_headers, org: Organization, <module_name>_data):
        response = client.post(
            f"/api/v1/<module_name>",
            json=<module_name>_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == <module_name>_data["name"]
        assert data["organization_id"] == org.id
        assert "id" in data

    def test_create_<module_name>_unauthorized(self, client: TestClient, <module_name>_data):
        response = client.post(f"/api/v1/<module_name>", json=<module_name>_data)
        assert response.status_code == 401

    def test_create_<module_name>_validation_error(self, client: TestClient, auth_headers):
        response = client.post(
            f"/api/v1/<module_name>",
            json={"name": ""},  # Invalid
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_list_<module_name>s(self, client: TestClient, auth_headers, org: Organization, sample_<module_name>):
        response = client.get(f"/api/v1/<module_name>", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(item["id"] == sample_<module_name>.id for item in data)

    def test_get_<module_name>_success(self, client: TestClient, auth_headers, sample_<module_name>):
        response = client.get(f"/api/v1/<module_name}/{sample_<module_name>.id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["id"] == sample_<module_name>.id

    def test_get_<module_name>_not_found(self, client: TestClient, auth_headers):
        response = client.get("/api/v1/<module_name>/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_<module_name>_success(self, client: TestClient, auth_headers, org: Organization, sample_<module_name>, <module_name>_update_data):
        # Need admin/owner role for update
        # Ensure test user has proper role in fixture
        response = client.patch(
            f"/api/v1/<module_name}/{sample_<module_name>.id}",
            json=<module_name>_update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["name"] == <module_name>_update_data["name"]

    def test_update_<module_name>_forbidden_for_member(self, client: TestClient, member_auth_headers, sample_<module_name>):
        """Member role cannot update."""
        response = client.patch(
            f"/api/v1/<module_name}/{sample_<module_name>.id}",
            json={"name": "Hack"},
            headers=member_auth_headers
        )
        assert response.status_code == 403

    def test_delete_<module_name>_success(self, client: TestClient, owner_auth_headers, sample_<module_name>):
        response = client.delete(f"/api/v1/<module_name}/{sample_<module_name>.id}", headers=owner_auth_headers)
        assert response.status_code == 204

    def test_cross_tenant_isolation(self, client: TestClient, auth_headers, other_org: Organization, db: Session):
        """User cannot access other organization's entities."""
        other_entity = <PascalCaseName>(name="Other Org", organization_id=other_org.id)
        db.add(other_entity)
        db.commit()
        
        response = client.get(f"/api/v1/<module_name}/{other_entity.id}", headers=auth_headers)
        assert response.status_code == 404  # Not found (not 403 to avoid info leak)
```

### 6. test_dependencies.py (RBAC/Feature Gating)
```python
# tests/modules/<module_name>/test_dependencies.py
import pytest
from fastapi import HTTPException
from api.modules.organizations.dependencies import require_org_role, require_feature
from api.modules.organizations.models import OrganizationMember, Organization, SubscriptionPlan
from api.modules.users.models import UserProfile

class Test<PascalCaseName>Dependencies:
    def test_require_org_role_owner(self, owner_membership: OrganizationMember):
        dep = require_org_role(["owner", "admin"])
        # Would need to test via actual route or mock Depends
        # This is a placeholder for integration test pattern

    def test_require_feature_gating(self, org_pro: Organization, org_starter: Organization):
        """Test feature gating works based on plan features."""
        # Pro has advanced_analytics, Starter doesn't
        assert "advanced_analytics" in (org_pro.subscription_plan.features or [])
        assert "advanced_analytics" not in (org_starter.subscription_plan.features or [])
```

## Running Generated Tests

```bash
# Run all tests for module
pytest tests/modules/<module_name>/ -v

# Run with coverage
pytest tests/modules/<module_name>/ --cov=api.modules.<module_name> --cov-report=term-missing

# Run specific test file
pytest tests/modules/<module_name>/test_services.py -v

# Run with markers
pytest tests/modules/<module_name>/ -m "not slow"
```

## Coverage Targets
- **Models**: 100% (simple ORM validation)
- **Schemas**: 100% (validation edge cases)
- **Services**: 90%+ (business logic, mock external calls)
- **Routes**: 80%+ (happy path + auth + validation + RBAC)
- **Dependencies**: 100% (RBAC matrix)

## Mock Patterns for External Services

### Mock Stripe Gateway
```python
# In test_services.py for billing-related services
class MockStripeGateway:
    def __init__(self):
        self.customers = {}
        self.subscriptions = {}
    
    def create_customer(self, email, name, metadata):
        return {"id": "cus_test_123", "email": email}
    
    def create_subscription(self, customer_id, price_id, payment_method, idempotency_key):
        return {"id": "sub_test_123", "status": "active", "current_period_end": 9999999999}
    
    def create_portal_session(self, customer_id, return_url):
        return "https://billing.stripe.com/session/test"
```

### Mock Email Sender
```python
# In conftest.py
@pytest.fixture
def mock_email_sender():
    sent_emails = []
    
    class MockSender:
        async def send(self, to, subject, template, context):
            sent_emails.append({"to": to, "subject": subject, "template": template, "context": context})
    
    return MockSender(), sent_emails
```

## Notes
- Always test organization isolation (cross-tenant access)
- Test all RBAC roles: owner, admin, member
- Test feature gating for each plan tier
- Mock ALL external services (Stripe, SES, Cognito)
- Use `TestClient` for integration tests, mock DB for unit tests
- Follow existing test naming: `test_<action>_<condition>_<expected>`