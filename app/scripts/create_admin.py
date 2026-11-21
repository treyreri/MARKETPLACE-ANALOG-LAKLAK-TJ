import argparse
import app.models  # noqa: F401  — регистрирует все модели
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.services.auth_service import get_user_by_phone
from app.utils.enums import RoleName
from app.utils.security import hash_password


def main():
    parser = argparse.ArgumentParser(description="Create an admin or grant admin role")
    parser.add_argument("phone_number")
    parser.add_argument("password", nargs="?", help="Required only for a new user")
    args = parser.parse_args()

    with SessionLocal() as db:
        user = get_user_by_phone(db, args.phone_number)

        if user is None:
            if not args.password:
                parser.error("password is required to create a new user")
            user = User(
                phone_number=args.phone_number,
                password_hash=hash_password(args.password),)
            db.add(user)

        if user.has_role(RoleName.ADMIN):
            print(f"{user.phone_number} is already an admin")
            return

        user.roles.append(UserRole(role=RoleName.ADMIN))
        db.commit()
        print(f"Admin role granted to {user.phone_number}")


if __name__ == "__main__":
    main()