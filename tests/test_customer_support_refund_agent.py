from python_sim import Simulation
from python_sim.errors import SimulationTimeoutError


def run_refund_agent(sim: Simulation, *, retry=False):
    email = sim.gmail.search("refund")[0]
    with sim.events.context(actor="customer-support-agent"):
        sim.gmail.mark_as_read(email.id)
        sim.events.emit("agent.email.read", {"email_id": email.id})
        order = sim.database.get_order("123")
        sim.events.emit("order.found", {"order_id": order.id, "order_number": order.number})
        try:
            payments = sim.stripe.list_payments(order_id=order.id)
        except SimulationTimeoutError:
            if not retry:
                raise
            sim.events.emit("agent.retry", {"operation": "stripe.list_payments"})
            payments = sim.stripe.list_payments(order_id=order.id)
        duplicate = payments[-1]
        sim.events.emit("payment.detected", {"payment_ids": [payment.id for payment in payments]})
        try:
            refund = sim.stripe.refund_payment(duplicate.id)
        except SimulationTimeoutError:
            if not retry:
                raise
            sim.events.emit("agent.retry", {"operation": "stripe.refund_payment"})
            refund = sim.stripe.refund_payment(duplicate.id)
        sent = sim.gmail.send_email(to=email.sender, subject="Your refund is complete", body="We refunded the duplicate charge.")
    return refund, sent


def seed_world(sim):
    customer = sim.database.create_customer(email="customer@example.com")
    order = sim.database.create_order(number="123", customer_id=customer.id, amount=5000, status="paid")
    sim.stripe.create_payment(customer_id=customer.id, amount=5000, order_id=order.id)
    sim.stripe.create_payment(customer_id=customer.id, amount=5000, order_id=order.id)
    sim.gmail.receive_email(from_="customer@example.com", subject="Refund request", body="Please refund my order #123. I was charged twice.")


def test_customer_support_refund_agent(sim):
    seed_world(sim)
    refund, sent = run_refund_agent(sim)
    payment = sim.stripe.get_payment(refund.payment_id)
    assert payment.status == "refunded"
    assert sim.stripe.get_refund(refund.id) == refund
    assert sent in sim.gmail.sent_mail()
    event_types = [event.type for event in sim.events.history()]
    assert event_types[-7:] == ["email.read", "agent.email.read", "order.found", "payment.detected", "refund.created", "payment.refunded", "email.sent"]
    assert all(event.correlation_id for event in sim.events.history()[-6:])

    snapshot = sim.snapshot()
    sim.stripe.refund_payment(sim.stripe.list_payments(order_id="123")[0].id)
    sim.restore(snapshot)
    assert sim.snapshot() == snapshot


def test_customer_support_agent_handles_stripe_timeout(sim):
    seed_world(sim)
    sim.stripe.fail_next("timeout")
    refund, sent = run_refund_agent(sim, retry=True)
    assert sim.stripe.get_payment(refund.payment_id).status == "refunded"
    assert sent in sim.gmail.sent_mail()
    assert "service.call.failed" in [event.type for event in sim.events.history()]
    assert "agent.retry" in [event.type for event in sim.events.history()]


def test_replay_is_identical():
    def execute(seed):
        sim = Simulation(seed=seed)
        seed_world(sim)
        run_refund_agent(sim)
        return sim.snapshot()

    assert execute(42) == execute(42)
    assert execute(42) != execute(43)
