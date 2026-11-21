from decimal import Decimal

from app.models import Order, OrderItem
from app.utils.enums import OrderStatus
from tests.conftest import auth


def test_statistics(client, db, make_product, make_seller, make_user, seller, seller_headers, category):
    a = make_product(seller, category, name="A", price=Decimal("10.50"), quantity=0)
    b = make_product(seller, category, name="B", price=Decimal("3"), is_active=False)
    other = make_seller(store_name="Other")
    foreign = make_product(other, category, name="F")
    buyer = make_user()

    def order(status, *lines):
        o = Order(user_id=buyer.id, recipient_name="x", phone_number="+992900000001", address="x",
                  total_price=Decimal("0"), status=status)
        o.items = [OrderItem(product_id=p.id, seller_id=p.seller_id, product_name=p.name,
                             price=p.price, quantity=q) for p, q in lines]
        db.add(o)

    order(OrderStatus.DELIVERED, (a, 2), (b, 1), (foreign, 5))
    order(OrderStatus.DELIVERED, (a, 1))
    order(OrderStatus.PENDING, (b, 4))
    order(OrderStatus.CANCELLED, (a, 7))
    order(OrderStatus.PENDING, (foreign, 1))
    db.commit()

    body = client.get("/seller/statistics", headers=seller_headers).json()
    assert (body["product_count"], body["active_product_count"], body["out_of_stock_count"]) == (2, 1, 1)
    assert body["units_sold"] == 4
    assert body["revenue"] == "34.50"
    assert body["order_count"] == 4
    assert body["orders_by_status"]["delivered"] == 2
    assert body["orders_by_status"]["pending"] == 1
    assert body["orders_by_status"]["cancelled"] == 1
    assert body["orders_by_status"]["shipped"] == 0


def test_statistics_empty(client, seller_headers):
    body = client.get("/seller/statistics", headers=seller_headers).json()
    assert (body["units_sold"], body["revenue"], body["order_count"]) == (0, "0.00", 0)


def test_statistics_only_for_sellers(client, customer):
    assert client.get("/seller/statistics", headers=auth(customer)).status_code == 403
