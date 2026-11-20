import enum
class RoleName(str, enum.Enum):
    SELLER = "seller"
    COURIER = "courier"
    ADMIN = "admin"
    