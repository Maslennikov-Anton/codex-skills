# Заметки По DOM

Текущие наблюдения по локальной сборке `ssh-configurator`:

- Приложение работает на Electron и отдаёт Chromium DevTools target, если запущено с `--remote-debugging-port`.
- Во время исследования наблюдался renderer route:
  `file:///usr/lib/ssh-configurator/resources/app/renderer/dist/index.html#/system-settings/datetime`
- Поле host в SSH-диалоге:
  - tag: `input`
  - id: `host-input`
- Действие подключения сейчас доступно через кнопку с видимым текстом:
  `Подключиться`

## Примечания

- В DOM есть PrimeVue-подобные классы, включая `p-inputtext`, `p-autocomplete-input` и `p-dialog-close-button`.
- Под GNOME Wayland/XWayland клики через `xdotool` оказались недостаточно надёжными для повторяемой автоматизации формы.
- AT-SPI экспортировал верхний Electron frame, но не дал полезного внутреннего дерева для этого диалога, поэтому accessibility-слой для целевого workflow оказался недостаточным.
