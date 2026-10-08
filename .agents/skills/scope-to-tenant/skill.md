# Skill: scope-to-tenant

## Description
Add organization-scoping (multi-tenancy isolation) to an existing query, service method, or repository. Ensures all data access is filtered by `organization_id` to prevent cross-tenant data leaks.

## Usage
```
/scope-to-tenant <target> [--type=query|service|repository]
```

## Examples
```
/scope-to-tenant "ProductService.get_all" --type=service
/scope-to-tenant "api/modules/products/services.py:get_user_products" --type=service
/scope-to-tenant "SELECT * FROM products WHERE organization_id = ?" --type=query
```

## Implementation Patterns

### Pattern 1: Service Method (Most Common)
**Before:**
```python
def get_all(self) -> List[Product]:
    return self.db.query(Product).all()
```

**After:**
```python
def get_all(self, organization_id: int) -> List[Product]:
    return self.db.query(Product).filter(Product.organization_id == organization_id).all()
```

### Pattern 2: Repository/Query Level
**Before:**
```python
stmt = select(Product).where(Product.is_active == True)
```

**After:**
```python
stmt = select(Product).where(
    Product.is_active == True,
    Product.organization_id == organization_id
)
```

### Pattern 3: Relationship Loading
**Before:**
```python
organization = db.query(Organization).options(
    selectinload(Organization.products)
).first()
```

**After:**
```python
organization = db.query(Organization).options(
    selectinload(Organization.products).where(Product.organization_id == organization_id)
).first()
```

## Checklist for Proper Scoping
- [ ] Every `query(Model)` adds `.filter(Model.organization_id == organization_id)`
- [ ] Every `select(Model)` adds `.where(Model.organization_id == organization_id)`
- [ ] Relationship loads use `.where()` on the relationship
- [ ] Bulk operations (update/delete) include organization_id filter
- [ ] Raw SQL (if any) uses parameterized `organization_id`
- [ ] Tests verify cross-tenant isolation

## Common Mistakes to Avoid
- ❌ Forgetting to pass `organization_id` from route to service
- ❌ Using `get_active_organization` but not passing `org.id` to service
- ❌ Scoping parent but not children (e.g., organization scoped but not its products)
- ❌ Using `current_user.id` instead of `organization_id` for tenant isolation

## Automatic Fixes
When applied, this skill will:
1. Find the target function/method
2. Add `organization_id: int` parameter
3. Add `.filter(Model.organization_id == organization_id)` to all queries
4. Update call sites to pass `org.id` from the route dependency
5. Add test case for cross-tenant isolation