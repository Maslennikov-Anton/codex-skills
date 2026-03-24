# Поля `openai.yaml` (полный пример и описания)

`agents/openai.yaml` это расширенный product-specific config, который предназначен для чтения машиной или harness, а не самим агентом. В папке `agents/` могут лежать и другие product-specific config-файлы.

## Полный пример

```yaml
interface:
  display_name: "Необязательное пользовательское имя"
  short_description: "Необязательное пользовательское описание"
  icon_small: "./assets/small-400px.png"
  icon_large: "./assets/large-logo.svg"
  brand_color: "#3B82F6"
  default_prompt: "Необязательный prompt-обрамляющий текст для использования skill-а"

dependencies:
  tools:
    - type: "mcp"
      value: "github"
      description: "MCP-сервер GitHub"
      transport: "streamable_http"
      url: "https://api.githubcopilot.com/mcp/"

policy:
  allow_implicit_invocation: true
```

## Описания полей и ограничения

Ограничения верхнего уровня:

- Заключай все строковые значения в кавычки.
- Ключи оставляй без кавычек.
- Для `interface.default_prompt` генерируй полезный короткий пример стартового prompt-а на основе skill-а, обычно в одно предложение. Он должен явно упоминать skill как `$skill-name`.
- По локальному правилу `interface.display_name`, `interface.short_description` и `interface.default_prompt` должны быть на русском, если пользователь явно не запросил другой язык.

- `interface.display_name`: пользовательский заголовок, который показывается в UI-списках skill-ов и на chips.
- `interface.short_description`: короткое пользовательское описание для быстрого сканирования, обычно 25-64 символа.
- `interface.icon_small`: путь к маленькому icon asset, относительный к skill dir. По умолчанию использовать `./assets/` и хранить иконки в папке `assets/`.
- `interface.icon_large`: путь к большому logo asset, относительный к skill dir. По умолчанию использовать `./assets/` и хранить иконки в папке `assets/`.
- `interface.brand_color`: hex-цвет для UI accent-ов, например badges.
- `interface.default_prompt`: prompt snippet по умолчанию, который вставляется при вызове skill-а.
- `dependencies.tools[].type`: категория зависимости. Сейчас поддерживается только `mcp`.
- `dependencies.tools[].value`: идентификатор инструмента или зависимости.
- `dependencies.tools[].description`: человекочитаемое описание зависимости.
- `dependencies.tools[].transport`: тип подключения, когда `type` равен `mcp`.
- `dependencies.tools[].url`: URL MCP-сервера, когда `type` равен `mcp`.
- `policy.allow_implicit_invocation`: если `false`, skill по умолчанию не подмешивается в model context, но его все еще можно вызвать явно через `$skill`.
  По умолчанию значение равно `true`.
