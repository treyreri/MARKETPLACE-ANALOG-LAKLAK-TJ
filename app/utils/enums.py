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


class TransportType(str, enum.Enum):
    FOOT = "foot"
    BICYCLE = "bicycle"
    MOTORCYCLE = "motorcycle"
    CAR = "car"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    CASH_ON_DELIVERY = "cash_on_delivery"



class DeliveryStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_DELIVERY = "in_delivery"
    DELIVERED = "delivered"