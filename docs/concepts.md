# Concepts

## Simulated world

The world is authoritative shared state. Customers, orders, payments, refunds, and emails are typed models. A Stripe refund changes the payment visible through later Stripe calls and through the order's payment relationships.

## Determinism

`Simulation(seed=42)` gives deterministic IDs. The simulated clock starts at a fixed UTC instant unless an explicit timezone-aware `start` is provided. Identical actions with the same seed produce equivalent snapshots and event histories.

## Services

The current release intentionally focuses on Gmail, the application database/order system, and Stripe. GitHub, Slack, and Calendar remain small secondary services. This is not a complete implementation of any third-party API.

## Mocks versus worlds

Mocks return configured answers to isolated calls. agent-world-sim models a world that changes after calls, allowing later agent actions to observe earlier consequences. It complements rather than replaces unit-test mocks.
