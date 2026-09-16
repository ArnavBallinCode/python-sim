# Testing agents

Use a pytest fixture to create an isolated simulation per test:

```python
import pytest
from python_sim import Simulation


@pytest.fixture
def sim():
    return Simulation(seed=42)


def test_refund_agent(sim):
    # Seed the customer/order/payment/email world, run the agent, then assert
    # payment, refund, sent-mail, and event state.
    ...
```

Snapshots provide an explicit checkpoint for branching or restoring state inside a test. Seeds make repeated test scenarios comparable. Fault injection lets the test verify application-owned retry behavior without waiting for real time or contacting a real provider.

The repository's [`test_customer_support_refund_agent.py`](https://github.com/ArnavBallinCode/python-sim/blob/main/tests/test_customer_support_refund_agent.py) is the reference end-to-end test.
