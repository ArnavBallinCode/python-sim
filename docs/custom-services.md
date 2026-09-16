# Custom services

Third-party services can be registered without changing `Simulation`:

```python
from python_sim.services import Service


class CRM(Service):
    name = "crm"

    def __init__(self):
        self.customers = {}

    def create_customer(self, customer_id, email):
        self.customers[customer_id] = {"email": email}
        return self.customers[customer_id]

    def snapshot_state(self):
        return {"customers": self.customers}

    def restore_state(self, data):
        self.customers = data["customers"]


sim.register_service("crm", CRM())
```

Registered services implement `bind`, `snapshot_state`, and `restore_state`. Their state is included in snapshots. Custom services should keep their state JSON-serializable if they need `save()`/`load()` support.
