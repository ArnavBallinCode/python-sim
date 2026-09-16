# Changelog

All notable changes to python-sim are documented here. The project follows a small subset of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and uses semantic versioning.

## [0.1.0] - 2026-09-16

### Added

- Deterministic, stateful local simulation with seeded IDs and a simulated UTC clock.
- Shared customer, order, payment, refund, and email world models.
- Gmail receive, search, read, delete, and send behavior, including sent-mail state.
- Order and payment relationships with duplicate-payment workflows.
- Stripe payment lookup, listing, refund creation, and refund state transitions.
- Causal events with timestamps, actors, correlation IDs, and causation IDs.
- Deterministic one-shot fault injection for timeouts, service failures, permissions, rate limits, and HTTP-style failures.
- Deep-copied, versioned snapshots with JSON save/load and restore validation.
- Framework-neutral agent tool descriptors with JSON schemas and side-effect metadata.
- Custom service registration with snapshot hooks.
- Canonical customer-support refund-agent example and pytest coverage.

### Scope

This release intentionally does not provide HTTP or browser simulation, cloud-service emulation, LangChain/MCP adapters, or a complete implementation of Gmail, Stripe, or other third-party APIs.
