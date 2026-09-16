# API reference

## Core

### `Simulation`

- `Simulation(seed=0, start=None)` — create a deterministic world. `start`, when supplied, must be timezone-aware.
- `clock.now()` — return the simulated UTC datetime.
- `clock.advance(seconds=..., minutes=..., hours=..., days=...)` — advance simulated time.
- `events.history(event_type=None)` — inspect event history.
- `events.on(event_type, handler)` — subscribe a runtime callback.
- `events.context(correlation_id=None, actor="agent")` — group a causal trace.
- `tools()` — return the agent tool registry.
- `snapshot()` / `restore(snapshot)` — checkpoint and restore the world.
- `save(path)` / `load(path)` — persist snapshots as JSON.
- `register_service(name, service)` — add a snapshot-aware custom service.

## Models

Public results are frozen dataclasses: `Customer`, `Order`, `Payment`, `Refund`, and `Email`. Their nested collections are tuples, so returned values cannot mutate the simulation.

## Errors

Expected simulator errors derive from `SimulationError`: `NotFoundError`, `ValidationError`, `PermissionDeniedError`, `ConflictError`, `ServiceUnavailableError`, `RateLimitError`, `SimulationTimeoutError`, `HttpError`, and `SnapshotError`.

See [Tools](tools.md) for the complete agent-facing operation list.
