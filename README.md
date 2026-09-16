# python-sim

`python-sim` is a deterministic local world for testing tool-using AI agents. It gives an agent simulated email, orders, payments, refunds, and a clock, so every action stays local and later actions observe earlier state changes.

Use it when a workflow has consequences across multiple steps: for example, an agent reads a refund request, finds an order, identifies a duplicate payment, refunds it, and sends confirmation. Use ordinary mocks for isolated unit tests where a fixed function response is all you need.

## 60-second example

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

email = sim.gmail.search("refund")[0]
sim.gmail.mark_as_read(email.id)
payments = sim.stripe.list_payments(order_id="123")
refund = sim.stripe.refund_payment(payments[-1].id)
confirmation = sim.gmail.send_email(
    to=email.sender, subject="Refund complete", body="Done"
)

assert sim.stripe.get_payment(refund.payment_id).status == "refunded"
assert confirmation in sim.gmail.sent_mail()
```

## Why python-sim instead of mocks?

A traditional mock usually models this:

```text
function/API call → predetermined response
```

python-sim models this:

```text
agent action → simulated world → state change → later action observes it
```

That makes it useful for:

- stateful multi-step workflows
- relationships across email, orders, and payments
- tool-using AI agents
- deterministic tests and replay
- injected failures and application-owned retries
- snapshots, branching scenarios, and debugging
- verifying the consequences of previous actions

It does not replace ordinary mocks. Keep using mocks for isolated units and simple dependency substitution; use python-sim when the behavior under test is the evolving world.

## Installation

`python-sim` is not published to PyPI yet. Install a built wheel:

```bash
python3 -m pip install /path/to/python_sim-0.1.0-py3-none-any.whl
```

After installation, examples run with the normal interpreter:

```bash
python3 examples/customer_support_agent.py
```

## Agent tools

`sim.tools()` returns a list of `Tool` descriptors. Each descriptor has:

- `name`: stable tool name
- `description`: text suitable for an agent prompt
- `schema`: JSON-schema input description
- `parameters`: alias for `schema`
- `side_effect`: whether calling it changes the simulated world
- `call(**arguments)`: invokes the tool and returns the service result
- `openai_schema()`: optional OpenAI-compatible function schema

```python
tools = sim.tools()
for tool in tools:
    print(tool.name, tool.schema, tool.side_effect)

refund_tool = next(tool for tool in tools if tool.name == "stripe.refund_payment")
refund = refund_tool.call(payment_id="payment-id")
```

Tool calls return typed models such as `Email`, `Order`, `Payment`, and `Refund`. They can raise the documented simulator errors below, as well as injected service failures. The agent/application decides whether to retry; python-sim only produces the configured failure.

### Available tools

| Name | Inputs | Returns | Side effect | Common errors |
| --- | --- | --- | --- | --- |
| `gmail.search` | `query: str` | `list[Email]` | No | injected service failures |
| `gmail.get_email` | `email_id: str` | `Email` | No | `NotFoundError` |
| `gmail.mark_as_read` | `email_id: str` | `Email` | Yes | `NotFoundError` |
| `gmail.send_email` | `to: str`, `subject: str`, `body: str` | `Email` | Yes | validation/injected failures |
| `database.get_order` | `order_id: str` (ID or number) | `Order` | No | `NotFoundError` |
| `database.find_payments` | `order_id: str` | `list[Payment]` | No | `NotFoundError` |
| `stripe.list_payments` | optional `order_id`, `customer_id` | `list[Payment]` | No | `NotFoundError` |
| `stripe.refund_payment` | `payment_id: str`, optional `amount: int` | `Refund` | Yes | `NotFoundError`, `ValidationError`, `ConflictError` |

## Customer-support agent example

The canonical runnable example is [`examples/customer_support_agent.py`](examples/customer_support_agent.py). It creates the world, inspects tool schemas, invokes tools, verifies the refunded payment and sent confirmation, snapshots/restores state, and prints the causal event types.

Representative output includes:

```text
available tools: gmail.search, gmail.get_email, gmail.mark_as_read, ...
payment status: refunded
sent confirmation: True
restored snapshot: True
```

## Failure injection and retry

Failures are deterministic and one-shot. The simulator injects the failure; the agent owns the retry policy.

```python
from python_sim import Simulation
from python_sim.errors import SimulationTimeoutError

sim = Simulation(seed=42)
sim.stripe.fail_next("timeout")

try:
    sim.stripe.list_payments(order_id="123")
except SimulationTimeoutError:
    # The application decides whether and how to retry.
    payments = sim.stripe.list_payments(order_id="123")
```

Supported failure values include `timeout`, `service_unavailable`, `permission_denied`, `429`, `500`, and integer HTTP status codes such as `500`.

## Causal events

Group agent actions into a trace:

```python
with sim.events.context(actor="customer-support-agent"):
    sim.events.emit("agent.email.read", {"email_id": email.id})
    sim.stripe.refund_payment(payment_id)

for event in sim.events.history():
    print(event.type, event.actor, event.correlation_id, event.causation_id)
```

Events contain an ID, type, simulated timestamp, payload, actor, correlation ID, and causation ID.

## State inspection

Service results are typed, frozen models; callers cannot mutate simulator state through them. Use service methods to inspect current state:

```python
payment = sim.stripe.get_payment(refund.payment_id)
refund = sim.stripe.get_refund(refund.id)
sent = sim.gmail.sent_mail()

assert payment.status == "refunded"
assert refund.status == "succeeded"
assert any(message.id == confirmation.id for message in sent)
```

## Snapshots, branching, and replay

Snapshots are detached deep copies of the world. They include service state, relationships, registered-service state, clock, ID counters, fault queues, and event history. Event handlers are intentionally not serialized and should be registered again after restore. JSON save/load uses snapshot version `2`.

```python
snapshot = sim.snapshot()

# Explore a branch without changing the checkpoint.
sim.gmail.receive_email(from_="debug@example.com", subject="branch")
sim.clock.advance(days=1)

sim.restore(snapshot)
assert sim.snapshot() == snapshot
```

This supports test isolation, branching scenarios, debugging, and deterministic replay:

```python
sim1 = Simulation(seed=42)
sim2 = Simulation(seed=42)

for current in (sim1, sim2):
    current.gmail.receive_email(from_="a@example.com", subject="hello")
    current.clock.advance(hours=1)

assert sim1.snapshot() == sim2.snapshot()
assert Simulation(seed=43).snapshot() != sim1.snapshot()
```

## Custom services

Services implement `bind`, `snapshot_state`, and `restore_state` and can be registered without editing `Simulation`:

```python
from python_sim.services import Service

class CRM(Service):
    name = "crm"

sim.register_service("crm", CRM())
```

## Development

Repository development uses the `src` layout. Build and test locally with:

```bash
python3 -m pip install -e '.[dev]'
python3 -m pytest
ruff check .
mypy src tests
python3 -m build --wheel
```

The runtime has no mandatory third-party dependencies.
