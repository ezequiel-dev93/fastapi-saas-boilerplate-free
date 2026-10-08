"""Script de sembrado de planes de suscripción, usuarios demo y organización para desarrollo."""
import api.models  # noqa: F401
from api.core.database import SessionLocal
from api.modules.billing.models import SubscriptionPlan
from api.modules.organizations.models import Organization, OrganizationMember
from api.modules.users.models import UserProfile, UserSettings


def seed():
    db = SessionLocal()
    try:
        plans = [
            {
                "name": "Gratuito",
                "slug": "free",
                "description": "Funcionalidades esenciales para creadores que están comenzando.",
                "price": 0.00,
                "interval": "monthly",
                "features": ["1 Proyecto", "Soporte comunitario", "Acceso a API con límite estándar"],
                "limits": {"ai_messages": 10, "members": 1, "api_keys": 2},
                "is_active": True,
            },
            {
                "name": "Pro Mensual",
                "slug": "pro-monthly",
                "description": "Ideal para profesionales y equipos en crecimiento.",
                "price": 19.99,
                "interval": "monthly",
                "features": [
                    "Proyectos Ilimitados",
                    "Soporte Prioritario por Email",
                    "Acceso Completo a la API",
                    "Analíticas Detalladas",
                ],
                "limits": {"ai_messages": 500, "members": 10, "api_keys": 10},
                "is_active": True,
            },
            {
                "name": "Pro Anual",
                "slug": "pro-yearly",
                "description": "Ahorra un 20% con facturación anual.",
                "price": 199.99,
                "interval": "yearly",
                "features": [
                    "Todo lo incluido en Pro Mensual",
                    "2 Meses Gratis de Bonificación",
                    "Soporte para Dominios Personalizados",
                ],
                "limits": {"ai_messages": 1000, "members": 20, "api_keys": 25},
                "is_active": True,
            },
            {
                "name": "Enterprise",
                "slug": "enterprise",
                "description": "Escalabilidad a medida, SLA y acompañamiento técnico dedicado.",
                "price": 499.00,
                "interval": "monthly",
                "features": [
                    "Infraestructura Dedicada",
                    "Garantía de SLA del 99.99%",
                    "Soporte 24/7",
                    "Contrato y Facturación Personalizada",
                ],
                "limits": {"ai_messages": 10000, "members": 100, "api_keys": 100},
                "is_active": True,
            },
        ]

        saved_plans = {}
        for plan_data in plans:
            existing = db.query(SubscriptionPlan).filter_by(slug=plan_data["slug"]).first()
            if not existing:
                plan = SubscriptionPlan(**plan_data)
                db.add(plan)
                db.flush()
                saved_plans[plan.slug] = plan
                print(f"Plan creado: {plan.name} (${plan.price}/{plan.interval})")
            else:
                existing.name = plan_data["name"]
                existing.description = plan_data["description"]
                existing.features = plan_data["features"]
                existing.limits = plan_data["limits"]
                saved_plans[existing.slug] = existing
                print(f"Plan actualizado: {existing.name}")

        # Demo users
        demo_users = [
            {
                "email": "admin@example.com",
                "cognito_sub": "dev-admin-sub-001",
                "first_name": "Juan",
                "last_name": "Admin",
                "plan_slug": "pro-monthly",
            },
            {
                "email": "member@example.com",
                "cognito_sub": "dev-member-sub-002",
                "first_name": "María",
                "last_name": "Member",
                "plan_slug": "free",
            },
        ]

        saved_users = {}
        for udata in demo_users:
            user = db.query(UserProfile).filter_by(email=udata["email"]).first()
            plan_obj = saved_plans.get(udata["plan_slug"])
            if not user:
                user = UserProfile(
                    email=udata["email"],
                    cognito_sub=udata["cognito_sub"],
                    first_name=udata["first_name"],
                    last_name=udata["last_name"],
                )
                db.add(user)
                db.flush()

                settings_obj = UserSettings(
                    user_id=user.id,
                    subscription_plan_id=plan_obj.id if plan_obj else None,
                    subscription_status="active" if udata["plan_slug"] != "free" else "inactive",
                )
                db.add(settings_obj)
                print(f"Usuario demo creado: {user.email}")
            else:
                user.first_name = udata["first_name"]
                user.last_name = udata["last_name"]
                if not user.settings:
                    settings_obj = UserSettings(
                        user_id=user.id,
                        subscription_plan_id=plan_obj.id if plan_obj else None,
                        subscription_status="active" if udata["plan_slug"] != "free" else "inactive",
                    )
                    db.add(settings_obj)
                print(f"Usuario demo existente: {user.email}")
            saved_users[udata["email"]] = user

        db.flush()

        # Demo Organization: Acme Corp
        admin_user = saved_users.get("admin@example.com")
        member_user = saved_users.get("member@example.com")
        pro_plan = saved_plans.get("pro-monthly")

        if admin_user:
            org = db.query(Organization).filter_by(slug="acme-corp").first()
            if not org:
                org = Organization(
                    name="Acme Corp",
                    slug="acme-corp",
                    owner_id=admin_user.id,
                    subscription_plan_id=pro_plan.id if pro_plan else None,
                    subscription_status="active",
                )
                db.add(org)
                db.flush()
                print(f"Organización demo creada: {org.name} (owner={admin_user.email})")
            else:
                org.owner_id = admin_user.id
                if pro_plan:
                    org.subscription_plan_id = pro_plan.id
                    org.subscription_status = "active"
                print(f"Organización demo existente: {org.name}")

            # Memberships
            # 1. Admin as owner
            admin_membership = (
                db.query(OrganizationMember)
                .filter_by(organization_id=org.id, user_id=admin_user.id)
                .first()
            )
            if not admin_membership:
                admin_membership = OrganizationMember(
                    organization_id=org.id,
                    user_id=admin_user.id,
                    role="owner",
                )
                db.add(admin_membership)

            # 2. Member as member
            if member_user:
                member_membership = (
                    db.query(OrganizationMember)
                    .filter_by(organization_id=org.id, user_id=member_user.id)
                    .first()
                )
                if not member_membership:
                    member_membership = OrganizationMember(
                        organization_id=org.id,
                        user_id=member_user.id,
                        role="member",
                    )
                    db.add(member_membership)

        db.commit()
        print("\n¡Sembrado (seed) completado con éxito!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

