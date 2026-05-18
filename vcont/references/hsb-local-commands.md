# VCont HSB Local Commands

Используй для локального stand `/home/ant/IdeaProjects/vcont-hsb`. Перед командами всё равно проверяй текущий repo layout и dirty worktree.

## Runtime

- Актуальный пакет: `vcont1/vcont.lin.x86_64.deb`.
- Generated runtime: `.work/vcont-runtime/vcontN/vcont-lin.x86_64-arch`.
- Старые `.tgz`, `.tar.gz` и распакованный `vcont1/vcont-lin.x86_64-arch` не являются источником правды.

## Prepare And Run

```bash
python3 scripts/prepare_vcont_runtime.py --count 2
docker compose up --build -d
COMPOSE_PROFILES=hsb-3plus docker compose up --build -d
COMPOSE_PROFILES=hsb-3plus,hsb-4 docker compose up --build -d
docker compose ps
docker compose logs -f
docker compose down
```

Для локального no-Docker smoke после prepare:

```bash
./.work/vcont-runtime/vcont1/vcont-lin.x86_64-arch/run-vcont.sh
```

## Tests

```bash
pytest
pytest --alluredir=allure-results
pytest -m "docker and not slow" --alluredir=allure-results
pytest tests/pytest_test/test_hsb_modbus_failover.py --alluredir=allure-results
pytest tests/pytest_test/test_hsb_modbus_failover.py::test_three_node_failover_continues_external_modbus_register_writes_twice --alluredir=allure-results
pytest -s tests/pytest_test/test_hsb_heartbeat_timing.py
HSB_HEARTBEAT_TIMING_ITERATIONS=10 pytest -s tests/pytest_test/test_hsb_heartbeat_timing.py
```

## Ports And Signals

- Docker Modbus server: `11.0.0.101:502`.
- Host Modbus server: `127.0.0.1:15020`.
- Modbus failover fboot writes synchronized counters to holding registers `2048..2050`.
- Assertions require no zero reset and step `+1` across takeover.
- Heartbeat timing report: `reports/hsb-heartbeat-timing/report.md`.
- Clean timing run should have `data_quality.duplicate_measurement_count == 0`.

## Reports

```bash
allure serve allure-results
```
