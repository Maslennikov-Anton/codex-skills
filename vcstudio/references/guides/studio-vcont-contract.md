# Studio/VCont Contract

This reference defines how VCStudio (front-end/project authoring layer) and VCont (back-end/runtime layer) fit together. It is duplicated into both skills so each side can reason about the handoff without loading the other skill first.

## Ownership Boundary

| Area | VCStudio owns | VCont owns |
|---|---|---|
| Project model | Workspace, `.vcsys`, project/device/resource/application/control-loop tree, GUI commands, properties | Runtime object names and containers created from generated commands |
| Authoring | Library browser, FB placement, ST editor, UserLibrary, connection drawing, order calculation UI | FB instantiation, connection execution, task scheduling, pin values |
| Load path | User commands `Загрузить`, `Онлайн загрузить КУ`, `Создать файл загрузки`, `Создать и загрузить файл загрузки`; `Консоль загрузки` output | IDE XML command handling, `LOADFILE`/bootfile execution, database creation, logs, responses |
| Runtime operations | Buttons/menus for connect, monitoring, live write, forcing, init/save variables, reset/reboot resource | Actual TCP session, value writes, forced values, warm/cold state, reset/reboot effects |
| Communication setup | Modbus Serial/TCP tables, OPC UA block editing, port publication fields | `Options="name=value ..."`, `MBSERVER`, `MBCLIENT*`, `MBSERIALPORT`, EIP/KNX/PROFIBUS device FBs, aliases, Modbus/OPC UA behavior, exposed memory/registers, diagnostics |
| Redundancy | Project must be loaded to each resource/node | HSB synchronizes runtime data/state, not project structure; current local role is exposed through `HSBSTATUS` |


## Terminology Alignment

- `Resource` in VCStudio is the front-end representation of a target VCont endpoint/instance: IP/port, load database, tasks, online operations, and communication settings belong under it.
- `Application` is the program namespace/group inside the resource. In runtime paths it appears as the application segment in names such as `APPLICATION1.LOOP1.FB`.
- `Control Loop` maps to a runtime subcontainer such as `APPLICATION1.LOOP1`; loops become executable only after assignment to a task.
- `Connection alias` in Studio UI is a visual/project convenience for references. It is not the same as VCont XML `Alias` used to bind FB ports to Modbus server registers.
- Prefer HSB terms `HSB_MAIN` and `HSB_RESERVE` in user-facing answers. Older/internal text may say `Master` and `Slave`; map `Master == HSB_MAIN`, `Slave == HSB_RESERVE`. Runtime `HSBSTATUS` returns simplified values: `MAIN`, `RESERVE`, `STANDALONE`, `NONE`.

## End-To-End Lifecycle

1. User creates/opens a VCStudio project (`.vcsys`) in a workspace.
2. User models `Device -> Resource -> Application -> Control Loop -> FBs`.
3. Resource stores target VCont IP/port; VC024SA uses default runtime port `61499`.
4. User assigns each control loop to a periodic or event task.
5. User defines FBs, initial values, data/event connections, execution order, Modbus/OPC UA mappings, and optionally ST blocks.
6. VCStudio converts the model into IDE XML commands and/or `vcont.fboot`.
7. VCont receives commands over TCP or reads `vcont.fboot` beside the executable.
8. VCont creates task resources, FB instances, connections, aliases, and starts tasks.
9. VCStudio can connect for monitoring, live writes, forcing, online loop load/delete, save/init variables, reset/reboot.
10. Tests/oracles should observe VCont runtime effects: Studio-like Watch monitoring, direct `READ` when explicitly marked as a runtime oracle, logs, Modbus/OPC UA outputs, HSB role/state, external devices.

## Object Mapping

| VCStudio concept | Runtime/bootfile manifestation |
|---|---|
| Resource IP/port | VCont TCP endpoint, usually configured through `IpPort` / resource properties |
| Application | Name prefix in runtime paths such as `APPLICATION1` |
| Control loop | Runtime subcontainer such as `APPLICATION1.LOOP1` |
| Function block instance | `CREATE <FB Name="APPLICATION1.LOOP1.FB" Type="..." />` |
| Initial value/literal write | `WRITE <Connection Source="literal" Destination="...PIN" />` |
| Data connection | `CREATE <Connection Source="...OUT" Destination="...IN" />` |
| Execution order | `CREATE` order and/or `ASSIGN <FB ... Before="..." />` |
| Task | `CREATE <FB Name="mainTask" Type="TASK_RES" Options="Period=... CPU=..." />` |
| Loop assigned to task | `task;<Request Action="ASSIGN"><Subcontainer Name="APP.LOOP" /></Request>` |
| Start task | `task;<Request Action="START" />` |
| Communication device options | Space-separated runtime `Options` string such as `Address=... Port=... SlaveId=...` |
| Modbus publication | Alias/port mapping to `MBSRV.REGISTER`, e.g. `MBSRV1.QX1` |


## Load Modes And Runtime Commands

| Studio action | Runtime interpretation | Notes |
|---|---|---|
| `Загрузить` resource/application/loop | Direct IDE command stream that creates/updates runtime database and starts relevant tasks | Full load disconnects Studio and writes initial values; next run is cold-start oriented. |
| `Создать файл загрузки` | Generate local `vcont.fboot` beside VCont executable | File contains the command set visible in `Консоль загрузки`; runtime reads it on startup. |
| `Создать и загрузить файл загрузки` | Generate bootfile and send it to controller, typically through load-file/execute-boot behavior | Success phrases: `The Load File command was sent successfully`, `Check BootSuccess`. |
| `Инициализация переменных` | `INITIALIZE`-class command | Clears warm-start data and restarts with initial values. |
| `Сохранение переменных` | `DBSAVE`-class command | Saves runtime DB/state for warm start; this is not `.vcsys` project save. |
| `Перезагрузка ресурса` | `REBOOT`-class command | Runtime/service restarts. |
| `Сброс ресурса` | `REMOVERES`-class command | Clears load database, deletes bootfile, restarts with initial values. |

Security note: protocol requirements mention signed `fboot` files and hash validation. Treat this as a product/security requirement unless current binaries and Studio flow are verified to enforce it.

## Load Semantics

- Full load of resource/application/loop disconnects Studio from the resource and writes initial values to VCont database. Next connection/start is treated as cold start.
- `Онлайн загрузить КУ` updates a control loop without replacing current runtime values with initial values.
- `Онлайн удалить КУ` deletes the loop algorithm from runtime; success is visible through generated `DELETE` commands and no console errors.
- `Создать файл загрузки` creates `vcont.fboot` in the VCont executable directory.
- `Создать и загрузить файл загрузки` creates the bootfile and sends it to controller; success phrases from VC024SA: `The Load File command was sent successfully` and `Check BootSuccess`.
- Runtime startup boot path requires `vcont.fboot` beside the executable unless a different bootfile path is configured.
- Generated programs must end with `START` for relevant tasks, otherwise created loops/FBs may exist but not execute.

## Ordering And Task Guardrails

- Order is behavior. Do not sort generated FBs or bootfile commands for readability.
- If block `B` must see block `A` output in the same cycle, create/order `A` before `B` or use explicit `ASSIGN Before`.
- Empty task executes nothing; each runnable loop must be assigned to a task.
- VCStudio says identical periods should not be assigned to different tasks; treat this as project-authoring guardrail and verify runtime behavior separately if needed.
- Event-loop flow should be explicit: `E_RESTART`/`START` -> `E_CYCLE` if needed -> sequential event-chain through FBs.
- Event branching creates undefined order; event cycles can drive resource load to 100%.

## Dependent User ST FB Types

- Treat each user-defined ST `FUNCTION_BLOCK` type as a separate translator input. A project may contain a dependency graph such as `TOP -> MIDDLE -> LEAF`, but concatenating those declarations into one `source_code.st` is unsupported.
- Discover the full dependency closure before load. Translate each type independently and emit `CREATE FBType` for every dependency and the root before assigning or starting the task. Preserve Studio's leaf-to-root topological order; reject a dependency cycle instead of silently choosing an order.
- A parent declaration such as `C : CHILD33;` is lowered to a persisted nested handle like `VCont.GetOrCreateFB("CHILD33", "C", fb)`. Nested instances belong to the parent instance and retain isolated state by instance name.
- Create a top-level runtime instance for the root type. Do not create top-level instances for dependencies unless the project model explicitly requires them; the parent creates its nested instances lazily during execution.
- Successful translation and successful `CREATE` of the parent `FBType` do not prove that the dependency exists. If a dependent type is absent at execution, VCont logs `Lua Lib create FB, type <TYPE> not found`, the nested handle is `nil`, and root outputs may remain at their initial values.
- Verify the root output after task execution with Studio-like Watch or an explicitly marked direct `READ` oracle. For stateful children, execute multiple cycles and assert the state sequence; for recursive composition, include a three-level chain.
- Keep composition separate from unsupported language features. Plain dependent FB instances are supported on the verified path; `EXTENDS`, `ABSTRACT`, `INTERFACE`/`IMPLEMENTS`, `METHOD`, user-defined `FUNCTION`, and POU `PROGRAM` require independent capability evidence.


## Online Loop Replace Skeleton

VCStudio states that `Онлайн загрузить КУ` preserves current values instead of resetting everything to initial values. At runtime this should be treated as a generated command sequence rather than a single magic operation. A safe interpretation is:

1. Identify affected loop, FBs, connections, aliases, and task assignment.
2. Stop only affected execution context if the generated command stream requires it.
3. Delete or replace obsolete FBs/connections/aliases.
4. Create new FBs/connections/aliases in behavior-preserving order.
5. Reassign the loop to the intended task if needed.
6. Start the relevant task(s).
7. Verify through `Консоль загрузки`, Studio-like Watch monitoring, an explicitly marked direct runtime `READ` oracle, logs, or external effects.

Do not assume all runtime state survives. Values on retained FB instances may survive; deleted/recreated FBs and changed pins may receive defaults or newly authored initial values. Verify against generated commands and current runtime behavior.

## State And Online Operations

- Initial values are a Studio-authored model, but actual current values live in VCont runtime/database.
- `Инициализация переменных` clears warm-start data and restarts with initial values.
- `Сохранение переменных` stores current parameters for warm start.
- Live value writes during monitoring are actual writes to VCont and affect the running algorithm.
- Forcing is not just UI highlighting: it changes runtime value selection and must be treated as a control action.
- Studio UI monitoring uses Watch lifecycle plus `READ <Watches/>`. Direct single-pin `READ` is a useful deterministic runtime oracle, but it is not the same protocol shape as Studio monitoring.
- Stopping a task before reading pins is a test stabilization technique only; do not present it as Studio monitoring behavior unless the specific UI action emits that command stream.


## Communication Artifact Mapping

| Studio setup | Generated/runtime artifact |
|---|---|
| Modbus TCP Server row | Runtime `MBSERVER` FB/options, for example `Address=... Port=... Mode=tcp SlaveId=...` |
| Modbus TCP Client row | Runtime `MBCLIENTTCP` options, for example `Address=... Port=502 SlaveId=... Window=1 Timeout=1000 HsbAlg=...` |
| Modbus Serial Port row | Runtime `MBSERIALPORT` options, for example `Device=/dev/ttyUSB0 Baud=9600 Parity=N DataBit=8 StopBit=1` |
| Modbus RTU Client row | Runtime `MBCLIENTRTU` options, for example `Port=... SlaveId=... Heartbeat=auto` |
| Modbus RTU-over-TCP Client row | Runtime `MBCLIENTRTUOVERTCP` options, for example `Address=... Port=502 SlaveId=... Timeout=1000` |
| FB port field `Modbus = MBSRV1.QX1` | Runtime Modbus alias/binding between FB port and server register |
| Modbus TCP/RTU client row | Runtime client/device configuration referenced by `_PACK` blocks through `DEVICE` |
| EtherNet/IP / KNX / PROFIBUS resource setup | Runtime `EIPDEV`, `KNXDEV`, `PRBDEV` options |
| `_PACK` block placed in loop | Runtime FB instance with `REQ`, `CNF`, `DEVICE`, `ENABLE`, `ADDRESS`, `FORMAT`, data pins, `STATUS` |
| OPC UA block `CLIENT`/`SUBSCRIBE`/`PUBLISH` | Runtime FB behavior driven by the `ID` string and internal/external OPC UA server/client settings |

OPC UA caveat: VC024SA says the internal OPC server is available automatically after runtime start, while VCont config notes `OpcuaServerPort` is relevant when the corresponding FB is used. Until verified on the current binary, answer conservatively: OPC UA server availability and port behavior depend on runtime config and active OPC UA blocks.

## Communication Contract

- Studio Modbus setup screens are front-end configuration. VCont runtime receives generated client/server FBs, aliases, and options.
- Runtime option strings use space-separated key-value pairs: `name1=value1 name2=value2`. Parameters with suitable defaults may be omitted; VCont then uses the default.
- `MBSERVER` memory areas are runtime surfaces; multiple servers have independent memory (`MBSRV1.QX1 != MBSRV2.QX1`).
- `MBCLIENTTCP.HsbAlg` is HSB-significant: `1` connects `MAIN`, `STANDALONE`, and `RESERVE` at startup; `2` connects only `MAIN` and `STANDALONE` at startup.
- Use `QX`/`IX` for Boolean publication when memory efficiency matters.
- `_PACK` blocks and diagnostic blocks must be verified against current typelibrary before writing strict tests because VC024SA has typos and reused write wording.
- OPC UA `CLIENT`, `SUBSCRIBE`, and `PUBLISH` are authored in Studio but runtime-facing through their `ID` strings and VCont's internal/external OPC UA behavior.


## HSB And Live Operations

- Loading or online-loading one Studio resource does not copy the project to reserve nodes. Each VCont node must receive the same or compatible generated program/bootfile.
- Live writes and forcing are runtime actions and may be sync triggers, but they do not synchronize project structure.
- HSB synchronization unit is runtime FB input/output data, not Studio project state and not necessarily event-task internal context.
- After failover, assert only synchronized DI/DO or external effects unless a broader state-sync guarantee was verified.
- Built-in `MBSERVER` alias patterns and external `MBWRITE` failover oracle patterns are different scenarios; do not transfer workaround rules blindly between them.
- Use VCont `HSBSTATUS` to read the current local HSB role of each runtime instance. `NONE` means HSB is disabled, not standalone failover behavior.

## HSB Contract

- HSB synchronizes runtime data/state, not the project, not `.vcsys`, not loop/task/FB structure.
- Each VCont node must be loaded with the same or compatible program before HSB behavior is meaningful.
- HSB tests should read `HSBSTATUS` for role selection and assert synchronized DI/DO or external effects, not Studio project state.
- For failover, separate immediate stop boundary from settled post-failover observations.

## Routing Rule

Use `vcstudio` skill when the user asks how to model/configure/click/edit in Studio, how a project is structured, or how the documentation describes UI flows.

Use `vcont` skill when the user asks what actually runs, what XML/bootfile/runtime behavior results, how to diagnose logs, how Modbus/OPC UA behaves at runtime, how HSB works, or how to test it.

Use both when translating a Studio operation into generated runtime artifacts or debugging a mismatch between Studio intent and VCont behavior.
