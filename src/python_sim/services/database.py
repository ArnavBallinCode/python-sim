from ..errors import ConflictError, NotFoundError, ValidationError
from ..models import Customer, Order, Payment
from .base import Service


class Database(Service):
    name = "database"

    def create_customer(self, *, email: str, name: str | None = None) -> Customer:
        self._before("create_customer")
        self._require_text(email, "email")
        if any(customer.email == email for customer in self.world.customers.values()):
            raise ConflictError(f"customer {email} already exists")
        customer = Customer(self.ids.new("customer"), email, name)
        self.world.customers[customer.id] = customer
        self.events.emit("customer.created", {"customer_id": customer.id})
        return customer

    def get_customer(self, customer_id: str) -> Customer:
        self._before("get_customer")
        try:
            return self.world.customers[customer_id]
        except KeyError as exc:
            raise NotFoundError(f"customer {customer_id} does not exist") from exc

    def create_order(self, *, number: str, customer_id: str, amount: int, currency: str = "usd", status: str = "pending") -> Order:
        self._before("create_order")
        self._require_text(number, "number")
        if amount <= 0:
            raise ValidationError("amount must be positive")
        self.get_customer(customer_id)
        if any(order.number == number for order in self.world.orders.values()):
            raise ConflictError(f"order {number} already exists")
        order = Order(self.ids.new("order"), number, customer_id, amount, currency.lower(), status, (), self.events.clock.now().isoformat())
        self.world.orders[order.id] = order
        self.events.emit("order.created", {"order_id": order.id, "order_number": number})
        return order

    def get_order(self, order_id: str) -> Order:
        self._before("get_order")
        order = self.world.orders.get(order_id) or next((o for o in self.world.orders.values() if o.number == order_id), None)
        if order is None:
            raise NotFoundError(f"order {order_id} does not exist")
        return order

    def list_orders(self, *, customer_id: str | None = None) -> list[Order]:
        self._before("list_orders")
        return [o for o in self.world.orders.values() if customer_id is None or o.customer_id == customer_id]

    def create_payment(self, *, order_id: str, amount: int, currency: str = "usd") -> Payment:
        self._before("create_payment")
        order = self.get_order(order_id)
        if amount <= 0:
            raise ValidationError("amount must be positive")
        payment = Payment(self.ids.new("payment"), order.customer_id, order.id, amount, currency.lower(), "succeeded", 0, self.events.clock.now().isoformat())
        self.world.payments[payment.id] = payment
        self.world.add_payment_to_order(order.id, payment.id)
        self.events.emit("payment.created", {"payment_id": payment.id, "order_id": order.id})
        return payment

    def find_payments(self, *, order_id: str) -> list[Payment]:
        self._before("find_payments")
        order = self.get_order(order_id)
        return [self.world.payments[payment_id] for payment_id in order.payment_ids]
