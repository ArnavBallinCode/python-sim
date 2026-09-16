"""Canonical local customer-support agent example.

Run after installation with: python3 examples/customer_support_agent.py
"""

from python_sim import Simulation


def seed_world(sim: Simulation) -> None:
    customer = sim.database.create_customer(email="customer@example.com")
    order = sim.database.create_order(number="123", customer_id=customer.id, amount=5000, status="paid")
    sim.stripe.create_payment(customer_id=customer.id, amount=5000, order_id=order.id)
    sim.stripe.create_payment(customer_id=customer.id, amount=5000, order_id=order.id)
    sim.gmail.receive_email(
        from_="customer@example.com",
        subject="Refund request",
        body="Please refund my order #123. I was charged twice.",
    )


def run_agent(sim: Simulation):
    tools = {tool.name: tool for tool in sim.tools()}
    print("available tools:", ", ".join(tools))
    print("refund schema:", tools["stripe.refund_payment"].schema)

    email = tools["gmail.search"].call(query="refund")[0]
    with sim.events.context(actor="customer-support-agent"):
        email = tools["gmail.get_email"].call(email_id=email.id)
        tools["gmail.mark_as_read"].call(email_id=email.id)
        order = tools["database.get_order"].call(order_id="123")
        payments = tools["database.find_payments"].call(order_id=order.id)
        duplicate = payments[-1]
        refund = tools["stripe.refund_payment"].call(payment_id=duplicate.id)
        confirmation = tools["gmail.send_email"].call(
            to=email.sender,
            subject="Your refund is complete",
            body="We refunded the duplicate charge.",
        )
    return refund, confirmation


if __name__ == "__main__":
    simulation = Simulation(seed=42)
    seed_world(simulation)
    refund, confirmation = run_agent(simulation)

    payment = simulation.stripe.get_payment(refund.payment_id)
    saved = simulation.snapshot()
    simulation.gmail.receive_email(from_="debug@example.com", subject="temporary mutation")
    simulation.restore(saved)

    print("payment status:", payment.status)
    print("refund status:", simulation.stripe.get_refund(refund.id).status)
    print("sent confirmation:", any(message.id == confirmation.id for message in simulation.gmail.sent_mail()))
    print("restored snapshot:", simulation.snapshot() == saved)
    print("events:", [event.type for event in simulation.events.history()])
