"""Import all SQLAlchemy models so Base.metadata knows about them."""

from api.core.database import Base
from api.modules.users.models import UserProfile, UserSettings

__all__ = [
    "Base",
    "UserProfile",
    "UserSettings",
]
