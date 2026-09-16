from ..errors import ConflictError, NotFoundError, ValidationError
from ..models import Customer, Payment, Refund
from .base import Service


class Stripe(Service):
    name = "stripe"

    def create_customer(self, *, email: str, name: str | None = None) -> Customer:
        self._before("create_customer")
        if any(customer.email == email for customer in self.world.customers.values()):
            return next(customer for customer in self.world.customers.values() if customer.email == email)
        customer = Customer(self.ids.new("customer"), email, name)
        self.world.customers[customer.id] = customer
        self.events.emit("stripe.customer.created", {"customer_id": customer.id})
        return customer

    def get_customer(self, customer_id: str) -> Customer:
        self._before("get_customer")
        try:
            return self.world.customers[customer_id]
        except KeyError as exc:
            raise NotFoundError(f"customer {customer_id} does not exist") from exc

    def create_payment(self, *, customer_id: str, amount: int, currency: str = "usd", order_id: str | None = None) -> Payment:
        self._before("create_payment")
        customer = self.get_customer(customer_id)
        if amount <= 0:
            raise ValidationError("amount must be positive")
        resolved_order_id = None
        if order_id:
            order = self.world.orders.get(order_id) or next((o for o in self.world.orders.values() if o.number == order_id), None)
            if order is None:
                raise NotFoundError(f"order {order_id} does not exist")
            if order.customer_id != customer.id:
                raise ConflictError("payment customer does not own order")
            resolved_order_id = order.id
        payment = Payment(self.ids.new("payment"), customer.id, resolved_order_id, amount, currency.lower(), "succeeded", 0, self.events.clock.now().isoformat())
        self.world.payments[payment.id] = payment
        if payment.order_id:
            self.world.add_payment_to_order(payment.order_id, payment.id)
        self.events.emit("payment.created", {"payment_id": payment.id, "order_id": payment.order_id})
        return payment

    def get_payment(self, payment_id: str) -> Payment:
        self._before("get_payment")
        try:
            return self.world.payments[payment_id]
        except KeyError as exc:
            raise NotFoundError(f"payment {payment_id} does not exist") from exc

    def list_payments(self, *, order_id: str | None = None, customer_id: str | None = None) -> list[Payment]:
        self._before("list_payments")
        resolved_order_id = None
        if order_id:
            order = self.world.orders.get(order_id) or next((o for o in self.world.orders.values() if o.number == order_id), None)
            if order is None:
                raise NotFoundError(f"order {order_id} does not exist")
            resolved_order_id = order.id
        return [p for p in self.world.payments.values() if (resolved_order_id is None or p.order_id == resolved_order_id) and (customer_id is None or p.customer_id == customer_id)]

    def refund_payment(self, payment_id: str, amount: int | None = None) -> Refund:
        self._before("refund_payment")
        payment = self.get_payment(payment_id)
        remaining = payment.amount - payment.refunded_amount
        amount = remaining if amount is None else amount
        if amount <= 0 or amount > remaining:
            raise ValidationError("refund amount must be positive and no greater than the remaining payment")
        if payment.status == "refunded":
            raise ConflictError(f"payment {payment_id} is already fully refunded")
        refund = Refund(self.ids.new("refund"), payment.id, amount, payment.currency, "succeeded", self.events.clock.now().isoformat())
        self.world.refunds[refund.id] = refund
        refunded_amount = payment.refunded_amount + amount
        status = "refunded" if refunded_amount == payment.amount else "partially_refunded"
        self.world.payments[payment.id] = Payment(payment.id, payment.customer_id, payment.order_id, payment.amount, payment.currency, status, refunded_amount, payment.created_at)
        self.events.emit("refund.created", {"refund_id": refund.id, "payment_id": payment.id, "amount": amount})
        self.events.emit("payment.refunded", {"payment_id": payment.id, "refund_id": refund.id})
        return refund

    def get_refund(self, refund_id: str) -> Refund:
        self._before("get_refund")
        try:
            return self.world.refunds[refund_id]
        except KeyError as exc:
            raise NotFoundError(f"refund {refund_id} does not exist") from exc
