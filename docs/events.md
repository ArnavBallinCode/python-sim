# Events

Use `sim.events.history()` to inspect the causal workflow:

```python
with sim.events.context(actor="customer-support-agent"):
    sim.events.emit("agent.email.read", {"email_id": email.id})
    sim.stripe.refund_payment(payment_id)

for event in sim.events.history():
    print(event.type, event.timestamp, event.actor)
    print(event.correlation_id, event.causation_id)
```

Each event contains:

- `event_id`
- `type`
- simulated UTC `timestamp`
- `payload`
- `actor`
- `correlation_id`
- `causation_id`

Event handlers can be registered with `sim.events.on(...)`. Handlers are runtime callbacks and are intentionally not included in snapshots.
