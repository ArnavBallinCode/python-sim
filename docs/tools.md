# Agent tools

`sim.tools()` returns `Tool` descriptors. Each descriptor provides:

- `name: str`
- `description: str`
- `schema: dict`, a JSON-schema input description
- `parameters`, an alias for `schema`
- `side_effect: bool`
- `call(**arguments)`, which invokes the tool
- `openai_schema()`, an optional OpenAI-compatible function schema

```python
tools = {tool.name: tool for tool in sim.tools()}
for tool in tools.values():
    print(tool.name, tool.schema, tool.side_effect)

email = tools["gmail.search"].call(query="refund")[0]
email = tools["gmail.get_email"].call(email_id=email.id)
tools["gmail.mark_as_read"].call(email_id=email.id)
```

## Available tools

| Name | Inputs | Returns | Side effect |
| --- | --- | --- | --- |
| `gmail.search` | `query: str` | `list[Email]` | No |
| `gmail.get_email` | `email_id: str` | `Email` | No |
| `gmail.mark_as_read` | `email_id: str` | `Email` | Yes |
| `gmail.send_email` | `to`, `subject`, `body` | `Email` | Yes |
| `database.get_order` | `order_id: str` | `Order` | No |
| `database.find_payments` | `order_id: str` | `list[Payment]` | No |
| `stripe.list_payments` | optional `order_id`, `customer_id` | `list[Payment]` | No |
| `stripe.refund_payment` | `payment_id`, optional `amount` | `Refund` | Yes |

Tools return typed models. They can raise `NotFoundError`, `ValidationError`, or `ConflictError` depending on the operation, plus configured fault-injection errors.
