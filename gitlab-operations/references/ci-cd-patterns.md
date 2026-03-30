# GitLab CI/CD patterns

Используй этот reference, когда задача касается проектирования, ревью или исправления `.gitlab-ci.yml`, а не операционной работы через `glab`.

## Базовая структура pipeline

```yaml
stages:
  - build
  - test
  - deploy
```

Минимальные правила:

- разделяй build/test/deploy на отдельные stages;
- артефакты передавай через `artifacts`, а не через повторную сборку без причины;
- кэш используй для ускорения, но не как замену артефактам;
- production deploy по умолчанию делай `manual`, если нет явно безопасного fully automated path.

## Что проектировать явно

- какие jobs блокируют merge или release;
- какие jobs можно кэшировать;
- какие артефакты нужны downstream jobs;
- какие переменные и секреты нужны pipeline;
- нужны ли отдельные staging/production environments;
- где нужны approval gates.

## Полезные паттерны

- branch-based deploy: staging от `develop`, production от `main`;
- Docker build/push через `CI_REGISTRY_*`;
- Terraform через `validate -> plan -> manual apply`;
- security includes для SAST/dependency/container scanning;
- child pipelines, если основной `.gitlab-ci.yml` уже перегружен.

## Практические правила

- Не смешивай проверочные и деплойные jobs без явной причины.
- Не делай production deploy автоматическим только ради удобства.
- Для больших pipeline-историй используй artifacts, rules и filters вместо копипасты job'ов.
- Если pipeline зависит от Kubernetes, Terraform или Docker, держи tool-specific детали в отдельных шаблонах или anchors.
