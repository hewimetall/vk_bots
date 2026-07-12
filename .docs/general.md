# Типы команд

- `info` просто выводит текст.
- `text` ожидает на вход текст новости.
- `media` ожидает на вход изображения.

# Файлы конфигурации

- `settings.ini` содержит ссылки на остальные конфигурационные файлы и токен VK.
- `commands.ini` содержит тексты сообщений и команд.
- `keyboards.ini` содержит подписи inline-кнопок.

# Настройка и запуск

1. Установите Python 3.12 и Poetry 2.x.
2. Установите зависимости:

   ```bash
   poetry install --no-root
   ```

3. Заполните `token` в `conf/settings.ini`.
4. Настройте переменные окружения:
   - `rabbitmq` - URL подключения RabbitMQ.
   - `QNAME` - имя очереди, по умолчанию `form_push`.
5. Запустите бота:

   ```bash
   poetry run python app.py
   ```

# Тесты и аудит

```bash
poetry run pytest
poetry run pytest --cov --cov-report=term-missing --cov-fail-under=93
poetry export -f requirements.txt --without-hashes -o /tmp/vk_bots_requirements.txt
poetry run pip-audit -r /tmp/vk_bots_requirements.txt
```