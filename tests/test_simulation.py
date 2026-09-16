import json

import pytest

from python_sim import NotFoundError, Simulation, SnapshotError, ValidationError
from python_sim.services.base import Service


def test_typed_results_are_immutable_and_stateful(sim):
    email = sim.gmail.receive_email(from_="a@example.com", subject="Meeting", body="Tomorrow")
    assert email.id.startswith("email_")
    assert email.read is False
    read = sim.gmail.mark_as_read(email.id)
    assert read.read is True
    assert sim.gmail.get_email(email.id).read is True
    with pytest.raises((AttributeError, TypeError)):
        read.read = False


def test_agent_tools_expose_explicit_email_read_and_schemas(sim):
    email = sim.gmail.receive_email(from_="a@example.com", subject="Hello")
    tools = {tool.name: tool for tool in sim.tools()}
    assert "gmail.get_email" in tools
    assert tools["gmail.get_email"].side_effect is False
    assert tools["gmail.get_email"].schema == tools["gmail.get_email"].parameters
    assert tools["gmail.get_email"].call(email_id=email.id) == email


def test_deterministic_snapshots():
    def run(seed):
        current = Simulation(seed=seed)
        customer = current.database.create_customer(email="a@example.com")
        current.database.create_order(number="1", customer_id=customer.id, amount=100)
        current.gmail.receive_email(from_="a@example.com", subject="hello")
        return current.snapshot()

    assert run(1) == run(1)
    assert run(1) != run(2)


def test_restore_rejects_bad_snapshots_without_mutating_world(sim):
    sim.gmail.receive_email(from_="a@example.com", subject="hello")
    before = sim.snapshot()
    bad = json.loads(json.dumps(before))
    bad["version"] = 999
    with pytest.raises(SnapshotError):
        sim.restore(bad)
    assert sim.snapshot() == before


def test_json_snapshot_preserves_typed_tuple_fields(sim, tmp_path):
    email = sim.gmail.receive_email(from_="a@example.com", to=["agent@example.com"], subject="hello")
    path = tmp_path / "world.json"
    sim.save(path)
    restored = Simulation(seed=999)
    restored.load(path)
    loaded = restored.gmail.get_email(email.id)
    assert isinstance(loaded.recipients, tuple)
    assert restored.snapshot() == sim.snapshot()


def test_custom_service_registration_is_first_class(sim):
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

    crm = sim.register_service("crm", CRM())
    crm.create_customer("c1", "a@example.com")
    snapshot = sim.snapshot()
    crm.customers.clear()
    sim.restore(snapshot)
    assert crm.customers["c1"]["email"] == "a@example.com"


def test_refund_validation_and_missing_resources(sim):
    with pytest.raises(NotFoundError):
        sim.stripe.get_payment("missing")
    customer = sim.database.create_customer(email="a@example.com")
    order = sim.database.create_order(number="1", customer_id=customer.id, amount=100)
    payment = sim.stripe.create_payment(customer_id=customer.id, amount=100, order_id=order.id)
    sim.stripe.refund_payment(payment.id)
    with pytest.raises(ValidationError):
        sim.stripe.refund_payment(payment.id)
