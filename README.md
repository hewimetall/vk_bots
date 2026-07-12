# VK Bots

VK Bots is a small VK chatbot service that collects a text submission,
optionally attaches photo URLs, and publishes the resulting feedback payload to
RabbitMQ.

## Requirements

- Python 3.12
- Poetry 2.x
- RabbitMQ when running the bot against a real queue

## Setup

Install project dependencies into a Poetry virtual environment:

```bash
poetry install --no-root
```

The project keeps runtime configuration in `conf/*.ini` files. The default
`conf/settings.ini` loads command text from `conf/commands.ini` and keyboard
labels from `conf/keyboards.ini`.

## Environment

Set these environment variables before running the bot:

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `rabbitmq` | Yes | empty string | RabbitMQ URL consumed by `pika.URLParameters`. |
| `QNAME` | No | `form_push` | Queue name used when publishing feedback payloads. |

The VK API token is read from the `token` value in `conf/settings.ini`.

## Run

After configuring `conf/settings.ini` and environment variables:

```bash
poetry run python app.py
```

## Test

Run the test suite:

```bash
poetry run pytest
```

Run coverage with the repository threshold:

```bash
poetry run pytest --cov --cov-report=term-missing --cov-fail-under=93
```

## Dependency audit

Audit the locked dependency set with pip-audit:

```bash
poetry export -f requirements.txt --without-hashes -o /tmp/vk_bots_requirements.txt
poetry run pip-audit -r /tmp/vk_bots_requirements.txt
```
