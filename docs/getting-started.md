# Getting started

## Installation

The first release is not yet published to PyPI. Install a built wheel:

```bash
python3 -m pip install /path/to/python_sim-0.1.0-py3-none-any.whl
```

The package has no mandatory runtime dependencies. The canonical example can then be run with:

```bash
python3 examples/customer_support_agent.py
```

## Create a world

```python
from python_sim import Simulation

sim = Simulation(seed=42)
customer = sim.database.create_customer(email="customer@example.com")
order = sim.database.create_order(number="123", customer_id=customer.id, amount=5000, status="paid")
sim.stripe.create_payment(customer_id=customer.id, amount=5000, order_id=order.id)
sim.stripe.create_payment(customer_id=customer.id, amount=5000, order_id=order.id)
sim.gmail.receive_email(
    from_="customer@example.com",
    subject="Refund request",
    body="Please refund my order #123. I was charged twice.",
)
```

The same customer, order, and payments are visible through the database and Stripe services. No network calls or credentials are involved.
