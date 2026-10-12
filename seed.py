"""Script de sembrado de usuarios demo para desarrollo en la edición Lite."""
import api.models  # noqa: F401
from api.core.database import SessionLocal
from api.modules.users.models import UserProfile, UserSettings


def seed():
    db = SessionLocal()
    try:
        # Demo users
        demo_users = [
            {
                "email": "admin@example.com",
                "cognito_sub": "dev-admin-sub-001",
                "first_name": "Juan",
                "last_name": "Admin",
                "subscription_status": "trial",
            },
            {
                "email": "member@example.com",
                "cognito_sub": "dev-member-sub-002",
                "first_name": "María",
                "last_name": "Member",
                "subscription_status": "inactive",
            },
        ]

        for udata in demo_users:
            user = db.query(UserProfile).filter_by(email=udata["email"]).first()
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
                    subscription_status=udata["subscription_status"],
                )
                db.add(settings_obj)
                print(f"Usuario demo creado: {user.email}")
            else:
                user.first_name = udata["first_name"]
                user.last_name = udata["last_name"]
                if not user.settings:
                    settings_obj = UserSettings(
                        user_id=user.id,
                        subscription_status=udata["subscription_status"],
                    )
                    db.add(settings_obj)
                print(f"Usuario demo existente: {user.email}")

        db.commit()
        print("\n¡Sembrado (seed) completado con éxito!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
