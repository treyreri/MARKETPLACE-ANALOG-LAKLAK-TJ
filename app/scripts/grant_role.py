import argparse
import app.models  # noqa: F401
from app.database import SessionLocal
from app.models.user import UserRole
from app.services.auth_service import get_user_by_phone
from app.utils.enums import RoleName


def main():
    parser = argparse.ArgumentParser(description="Grant a role to an existing user")
    parser.add_argument("phone_number")
    parser.add_argument("role", choices=[r.value for r in RoleName])
    args = parser.parse_args()
    role = RoleName(args.role)

    with SessionLocal() as db:
        user = get_user_by_phone(db, args.phone_number)
        if user is None:
            parser.error(f"user {args.phone_number} not found")
        if user.has_role(role):
            print(f"{user.phone_number} already has role {role.value}")
            return
        user.roles.append(UserRole(role=role))
        db.commit()
        print(f"Role {role.value} granted to {user.phone_number}")


if __name__ == "__main__":
    main()