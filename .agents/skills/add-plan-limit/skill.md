# Skill: add-plan-limit

## Description
Add feature gating / plan-based limits to restrict functionality based on the organization's subscription plan. Uses the existing `require_feature` dependency and `SubscriptionPlan.features` JSON field.

## Usage
```
/add-plan-limit <feature_name> <plan_names> [--endpoint=<route>] [--service=<method>]
```

## Examples
```
/add-plan-limit "advanced_analytics" "pro,enterprise" --endpoint=POST /api/v1/analytics/report
/add-plan-limit "api_access" "starter,pro,enterprise" --service=ApiService.make_request
/add-plan-limit "white_label" "enterprise" --endpoint=GET /api/v1/settings/branding
```

## Implementation Steps

### 1. Define Feature in Subscription Plan
Update `seed.py` or create migration to add feature to plan's `features` list:

```python
# In seed.py or migration
plans = [
    {
        "name": "Starter",
        "stripe_price_id": "price_starter",
        "features": ["api_access", "basic_reports"],  # Add new feature here
        "limits": {"api_calls": 10000, "team_members": 5}
    },
    {
        "name": "Pro",
        "stripe_price_id": "price_pro",
        "features": ["api_access", "basic_reports", "advanced_analytics", "custom_integrations"],
        "limits": {"api_calls": 100000, "team_members": 25}
    },
    {
        "name": "Enterprise",
        "stripe_price_id": "price_enterprise",
        "features": ["api_access", "basic_reports", "advanced_analytics", "custom_integrations", "white_label", "sso"],
        "limits": {"api_calls": 1000000, "team_members": 100}
    }
]
```

### 2. Add Dependency to Route
```python
from api.modules.organizations.dependencies import require_feature

@router.post("/analytics/report")
async def generate_report(
    data: ReportRequest,
    membership: OrganizationMember = Depends(require_feature("advanced_analytics")),
    # ... other deps
):
    # Only accessible if org's plan has "advanced_analytics" in features
    return analytics_service.generate(data, membership.organization_id)
```

### 3. Add Service-Level Check (Optional)
For more granular control or custom error messages:

```python
from api.modules.organizations.models import Organization
from fastapi import HTTPException, status

def check_feature_access(org: Organization, feature: str) -> bool:
    """Check if organization's plan includes a feature."""
    if not org.subscription_plan:
        return False
    if org.subscription_status not in ("active", "trialing"):
        return False
    return feature in (org.subscription_plan.features or [])

# In service method
def generate_report(self, organization_id: int, data: ReportRequest) -> Report:
    org = self.db.query(Organization).get(organization_id)
    if not check_feature_access(org, "advanced_analytics"):
        raise HTTPException(
            status_code=403,
            detail="This feature requires a Pro or Enterprise plan"
        )
    # ... generate report
```

### 4. Frontend Feature Flag (OpenAPI)
The feature is automatically exposed via the OpenAPI spec. Frontend can check:
```typescript
// Generated from openapi.json
interface Organization {
  subscription_plan: {
    features: string[];  // ["api_access", "advanced_analytics", ...]
  }
}

// In React component
const { organization } = useOrganization();
const canAccessAnalytics = organization?.subscription_plan?.features?.includes("advanced_analytics");

{canAccessAnalytics && <AnalyticsTab />}
```

## Plan Limits (Quantitative)
For numeric limits (API calls, team members, storage), use the `limits` JSON field:

```python
# In service
def check_limit(org: Organization, limit_key: str, current_usage: int) -> bool:
    if not org.subscription_plan:
        return False
    limits = org.subscription_plan.limits or {}
    max_allowed = limits.get(limit_key, 0)
    return current_usage < max_allowed

# Usage
if not check_limit(org, "api_calls", current_month_calls):
    raise HTTPException(403, "API call limit exceeded. Upgrade your plan.")
```

## Testing
Add test cases:
```python
def test_feature_gating_denies_access_for_lower_plan(client, org_starter, auth_headers):
    # Starter plan doesn't have advanced_analytics
    response = client.post("/api/v1/analytics/report", json={}, headers=auth_headers)
    assert response.status_code == 403
    assert "advanced_analytics" in response.json()["detail"]

def test_feature_gating_allows_access_for_pro_plan(client, org_pro, auth_headers_pro):
    response = client.post("/api/v1/analytics/report", json={}, headers=auth_headers_pro)
    assert response.status_code == 200
```

## Migration for Existing Plans
```bash
# Create migration to add feature to existing plans
alembic revision -m "add advanced_analytics feature to pro and enterprise plans"
```

```python
# In migration
def upgrade():
    from sqlalchemy import text
    # Update Pro plan
    op.execute(text("""
        UPDATE subscription_plans 
        SET features = jsonb_set(features, '{features}', features || '["advanced_analytics"]')
        WHERE name = 'Pro'
    """))
    # Update Enterprise plan
    op.execute(text("""
        UPDATE subscription_plans 
        SET features = jsonb_set(features, '{features}', features || '["advanced_analytics"]')
        WHERE name = 'Enterprise'
    """))
```

## Notes
- Features are stored as JSON array in `SubscriptionPlan.features`
- `require_feature` checks: plan exists + status active/trialing + feature in list
- Use descriptive feature names: `snake_case`, lowercase
- Document features in `docs/guides/stripe-setup.md` pricing table