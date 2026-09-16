# agent-world-sim

agent-world-sim is a deterministic local world for testing tool-using AI agents. It is designed for workflows where one action changes what a later action can observe.

The focused example is a customer-support agent that:

1. reads a refund request
2. finds order `123`
3. discovers duplicate payments
4. refunds one payment
5. sends confirmation
6. snapshots and replays the resulting world

Use ordinary mocks for isolated units. Use agent-world-sim when the thing under test is the evolving state and consequences of a multi-step tool workflow.

```python
from python_sim import Simulation

sim = Simulation(seed=42)
customer = sim.database.create_customer(email="customer@example.com")
order = sim.database.create_order(number="123", customer_id=customer.id, amount=5000)
sim.stripe.create_payment(customer_id=customer.id, amount=5000, order_id=order.id)
sim.gmail.receive_email(from_="customer@example.com", subject="Refund", body="Refund order #123")
```

Continue with [Getting started](getting-started.md) or run the canonical [`examples/customer_support_agent.py`](https://github.com/ArnavBallinCode/python-sim/blob/main/examples/customer_support_agent.py).
