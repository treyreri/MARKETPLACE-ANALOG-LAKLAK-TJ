import enum
class RoleName(str, enum.Enum):
    SELLER = "seller"
    COURIER = "courier"
    ADMIN = "admin"

class Language(str, enum.Enum):
    RU = "ru"
    EN = "en"