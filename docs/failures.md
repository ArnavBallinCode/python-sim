# Failure injection

The simulator injects failures; the agent or application owns the retry policy.

```python
from python_sim import Simulation
from python_sim.errors import SimulationTimeoutError

sim = Simulation(seed=42)
sim.stripe.fail_next("timeout")

try:
    sim.stripe.list_payments(order_id="123")
except SimulationTimeoutError:
    payments = sim.stripe.list_payments(order_id="123")
```

Failures are deterministic and one-shot. Supported values include:

- `timeout` → `SimulationTimeoutError`
- `service_unavailable` → `ServiceUnavailableError`
- `permission_denied` → `PermissionDeniedError`
- `429` or `rate_limited` → `RateLimitError`
- `500` or integer HTTP status codes → `HttpError`

Failures can be queued on a service with `service.fail_next(...)`. A failed call emits `service.call.failed` before raising.
