# Snapshots and replay

```python
snapshot = sim.snapshot()

sim.gmail.receive_email(from_="debug@example.com", subject="temporary")
sim.clock.advance(days=1)

sim.restore(snapshot)
assert sim.snapshot() == snapshot
```

Snapshots are detached deep copies. They include world state, relationships, registered-service state, clock, ID counters, fault queues, and event history. Mutating the live world after taking a snapshot does not mutate the snapshot.

Snapshots can be persisted as JSON:

```python
sim.save("world.json")
sim.load("world.json")
```

Snapshot version `2` is supported. Invalid or incompatible snapshots raise `SnapshotError` and are rejected without partially applying the restore. Event handlers are intentionally not serialized; register them again after restoring.

Snapshots are useful for test isolation, branching a scenario, debugging a failing agent, and replaying a deterministic workflow.

## Same-seed replay

```python
sim1 = Simulation(seed=42)
sim2 = Simulation(seed=42)

for current in (sim1, sim2):
    current.gmail.receive_email(from_="a@example.com", subject="hello")
    current.clock.advance(hours=1)

assert sim1.snapshot() == sim2.snapshot()
```

A different seed changes deterministic IDs and therefore the resulting snapshot where those IDs are present.
