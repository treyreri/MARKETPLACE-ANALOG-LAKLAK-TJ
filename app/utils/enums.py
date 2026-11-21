import enum
class RoleName(str, enum.Enum):
    SELLER = "seller"
    COURIER = "courier"
    ADMIN = "admin"

class Language(str, enum.Enum):
    RU = "ru"
    EN = "en"



class ProductSort(str, enum.Enum):
    NEWEST = "newest"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"