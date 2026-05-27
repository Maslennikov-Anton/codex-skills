# VCStudio Source Repo Map

Этот reference описывает локальный исходный проект
`/home/ant/IdeaProjects/vcstudio` как codebase. Используй его, когда вопрос
касается сборки VCStudio, структуры plugins/features/tests, product packaging,
custom `ru.isource.*` bundles, EMF-модели, DTO/JSON слоя или CI/release.

Для пользовательской работы в IDE продолжай использовать `project-workflow.md`,
`loading-monitoring.md`, `communications.md`, `st-language.md` и
`fb-typelibrary.md`. Для фактического runtime-поведения VCont переходи через
`studio-vcont-contract.md` в `vcont` skill.

## Current Verified Snapshot

Проверено по исходникам на 2026-05-27:

- repo root: `/home/ant/IdeaProjects/vcstudio`;
- parent Maven coordinates: `org.eclipse.fordiac:parent:1.22.8-SNAPSHOT`;
- product version: `1.22.8.qualifier`;
- Tycho version: `2.7.5`;
- Java source/required execution environment: Java 17 for repo/custom bundles;
- Eclipse target repository: `https://download.eclipse.org/releases/2021-06`;
- JustJ JRE repository: Java 17 `17.0.14`;
- product id: `org.eclipse.fordiac.ide.product`;
- application id: `org.eclipse.fordiac.ide.vcsapplication`;
- launcher name/root folder: `vcstudio`;
- product build outputs under
  `plugins/org.eclipse.fordiac.ide.product/target/products/`.

`docs.md` in the repo is useful as an orientation note, but verify drift-prone
facts against `pom.xml`, product files, manifests and CI. In the current local
snapshot `docs.md` still mentions `1.22.7`, while the build/product files are
`1.22.8`.

## Build And Module Layout

Root files:

- `pom.xml` is the parent Tycho build.
- `.mvn/extensions.xml` enables `org.eclipse.tycho.extras:tycho-pomless:1.5.1`.
- `plugins/pom.tycho`, `features/pom.tycho`, `tests/pom.tycho` list
  automatically discovered Tycho modules.
- `.gitlab-ci.yml` defines manual test/build/release jobs.

Main module areas:

- `plugins/`: implementation bundles and the final product project.
- `features/`: installable feature groups.
- `tests/`: Tycho test bundles.
- `data/`: documentation, templates, icons, ST/Lua sample, keys and FB
  typelibrary.
- `VCSLicense/`: auxiliary Maven module for license UI tooling.

Trusted local commands from repo evidence:

```bash
mvn test
mvn install -Dmaven.test.skip=true -Dtycho.disableP2Mirrors=true
mvn clean verify
```

Use network-aware judgement: these commands resolve Maven/p2 dependencies and
can be slow. For skill edits, validate the skill itself; do not run full VCStudio
build unless the user asks or the task requires it.

## Product Packaging

Product definition:

- `plugins/org.eclipse.fordiac.ide.product/org.eclipse.fordiac.ide.product`
- `plugins/org.eclipse.fordiac.ide.product/org.eclipse.fordiac.ide.product.target`
- `plugins/org.eclipse.fordiac.ide.product/org.eclipse.fordiac.ide.product.build.target`
- `plugins/org.eclipse.fordiac.ide.product/pom.xml`

Important launcher/runtime settings from the product file:

- UI locale is forced with `-nl ru`.
- Startup uses `-clean`.
- File encoding is `UTF-8`.
- JVM memory: `-Xmn512m`, `-Xms1024m`, `-Xmx5120m`.
- GC flags include G1 and string deduplication.
- `-DserverURL=https://localhost:9443`.
- `-DDB_MODE=false`.

The product includes Eclipse platform/p2/EMF/Xtext/JDT/EGit/JGit/JustJ/ELK/Babel
features plus VCStudio feature groups:

- `org.eclipse.fordiac.ide.comgeneration.feature`
- `org.eclipse.fordiac.ide.deployment.feature`
- `org.eclipse.fordiac.ide.export.feature`
- `org.eclipse.fordiac.ide.runtime.feature`
- `org.eclipse.fordiac.ide.typeeditor.feature`
- `org.eclipse.fordiac.ide.workbench.feature`

## Feature And Plugin Responsibilities

Feature projects:

- `workbench.feature`: broad base layer and custom `ru.isource.*` bundles.
- `typeeditor.feature`: FB/type editors.
- `deployment.feature`: deployment, monitoring and online edit support.
- `export.feature`: export/generation pipeline.
- `runtime.feature`: runtime launchers/execution support.
- `comgeneration.feature`: communication FB generation tools.

Major upstream-style plugin groups:

- model: `org.eclipse.fordiac.ide.model`, `.edit`, `.ui`, `.commands`;
- editors: `fbtypeeditor*`, `datatypeeditor`, `subapptypeeditor`,
  `resourceediting`;
- deployment/runtime: `deployment*`, `monitoring`, `onlineedit`, `runtime`;
- export: `export`, `export.ui`, `export.compare`, `export.forte_ng`,
  `export.forte_lua`;
- app/UI: `org.eclipse.fordiac.ide`, `.application`, `.ui`, `.images`, `.gef`;
- language tooling: `model.structuredtext*`, `model.xtext.fbt*`;
- utilities: `util`, `metrics`, `validation`.

Custom bundles are included through `workbench.feature`:

- `ru.isource.ide`
- `ru.isource.ide.quicksearch`
- `ru.isource.configurator`
- `ru.isource.ide.help`

## Custom ru.isource Bundles

`ru.isource.ide`:

- shared custom base bundle;
- exports `ru.isource.ide`, `ru.isource.ide.proxy`,
  `ru.isource.ide.proxy.model`, `ru.isource.ide.security`,
  `ru.isource.ide.ui.services`;
- embeds Jackson `2.19.0`, JJWT `0.12.6`, BouncyCastle `1.81`;
- has `MonitoringEnabledTester` registered through
  `org.eclipse.core.expressions.propertyTesters`;
- `HttpClientProxy` chooses `serverURL` from system property, defaulting to
  `https://localhost:9443` in prod and `http://localhost:8080` otherwise;
- authenticated requests send `Authorization: Bearer <jwt>` and optionally
  `VC-Project-Name`.

`ru.isource.configurator`:

- SSH/configurator integration bundle;
- exports `ru.isource.configurator`, `.dialogs`, `.services`;
- embeds `ru.isource.ssh.configurator-1.17`, `jsch-0.2.20`, SnakeYAML `2.3`,
  Log4j and SLF4J libraries;
- `ConnectionService` creates/reuses SSH connections by `ip:port`, default SSH
  port `22`;
- `ConfiguratorResourceService` stores user/ip/port/keyFile preferences under
  `ru.isource.configurator.resources...`;
- parses CIDR IPv4 addresses into address/netmask for `NetworkInterface`.

`ru.isource.ide.quicksearch`:

- registers command `ru.isource.ide.quicksearch.commands.openDialog`;
- contributes the command into the Eclipse `Edit` menu;
- implementation centers on `QuickSearchHandler`,
  `VCStudioQuickSearchDialog`, table label providers and `Searcher`.

`ru.isource.ide.help`:

- contributes view `org.eclipse.help.ui.HelpView`;
- adds a Help menu command `ru.isource.ide.help.ShowHelpView`;
- key binding: `F1` on Windows, `M2+F1` on GTK;
- embeds VCStudio and VCSystem PDF docs plus PDFBox `3.0.5` libraries.

## VCStudio EMF Model And DTO Layer

The VCStudio-specific hierarchy is modeled under the `vcstudioElement`
subpackage in:

- `plugins/org.eclipse.fordiac.ide.model/model/lib.ecore`
- generated Java under
  `plugins/org.eclipse.fordiac.ide.model/src-gen/org/eclipse/fordiac/ide/model/libraryElement/vcstudioElement/`

Core classes/relations:

- `Project`: `description`, contains `devices`.
- `Device`: `description`, `model`, contains `resources`, has
  `systemProperties`.
- `Resource`: `description`, `ip`, `port`, `cpu`, `deploymentStatus`,
  contains `applications`, `tasks`, `topLevelInterfaces`,
  `fieldLevelInterfaces`, `ethernetDevices`, `modbusSerialPorts`,
  `modbusRTUClients`, references `settings` and `profibusMasters`.
- `Application`: `description`, `deploymentStatus`, contains `loops`.
- `Task`: `interval`, `number`, belongs to `Resource`.
- `Loop`: `description`, `task`, required `FBNetwork`, belongs to
  `Application`, `deploymentStatus` default `Not_Deployed`.
- `NetworkInterface`: `address`, `subnetwork`, `gateway`, `port`,
  `description`.
- `EthernetDevice`: `priority`, `period`, `rtFormat`, `ip`, `interface`,
  `options`, `cpu`.
- `ResourceSettings`: `address`, `logLevel`, `queueSize`, `opcUaPort`,
  `diagnosticPeriod`, `saveInterval`, `warmStart`, `saveOutputsFb`, `useTls`,
  `useAuth`, `licenseFile`, `publicKey`.
- Modbus/Profibus model: `ModbusSerialPort`, `ModbusRTUClient`,
  `ProfibusMaster`, `ProfibusSlave`, `ProfibusModule`.

DTO/JSON integration lives in:

- `plugins/org.eclipse.fordiac.ide.model/src/org/eclipse/fordiac/ide/model/dto/`
- `plugins/org.eclipse.fordiac.ide.model/src/org/eclipse/fordiac/ide/model/dto/impl/`
- `plugins/org.eclipse.fordiac.ide.model/src/org/eclipse/fordiac/ide/model/json_processing/`

Key files:

- `ProjectSerializer.java`
- `ProjectDeserializer.java`
- `ElementCollector.java`
- DTOs for `Project`, `Device`, `Resource`, `Application`, `Loop`, `Task`,
  `FB`, `Connection`, `ST`, `ResourceSettings`, Modbus, KNX and Profibus.

Use this layer when analyzing DB/API sync, project import/export JSON, or why a
VCStudio field does or does not survive serialization.

## Import, Export, Type Library

Model import/export code:

- `dataimport/*Importer.java`
- `dataexport/*Exporter.java`
- `ProjectImporter` / `ProjectExporter`
- `SystemImporter` / `SystemExporter`
- `FbtExporter`, `FBTImporter`, `DataTypeImporter`, `SubAppTImporter`

Type library loading and palette integration:

- `typelibrary/TypeLibrary.java`
- `typelibrary/DataTypeLibrary.java`
- `typelibrary/EventTypeLibrary.java`
- `typelibrary/Create*PaletteEntry.java`

For concrete block pin/event/type information, use
`fb-typelibrary.md` and `fb-typelibrary-catalog.md`; do not infer pins from
Java class names.

## Deployment, Online Edit, Monitoring

Important source areas:

- `plugins/org.eclipse.fordiac.ide.deployment`
- `plugins/org.eclipse.fordiac.ide.deployment.iec61499`
- `plugins/org.eclipse.fordiac.ide.deployment.ui`
- `plugins/org.eclipse.fordiac.ide.onlineedit`
- `plugins/org.eclipse.fordiac.ide.monitoring`

Online edit handlers call `IDeviceManagementInteractor` operations for creating
FB instances, connections and starting FBs. Treat these as Studio-side command
invocation points; runtime XML command semantics still belong to `vcont`.

FB order calculation source:

- `deployment/FBOrderCalculationHelper.java`
- `deployment/SafeFBOrderCalculationHelper.java`
- `deployment/order/OrderGraphBuilder.java`
- `deployment/order/OrderEngine.java`
- `deployment/order/OrderNode.java`
- `deployment/order/OrderEdge.java`
- `deployment/order/OrderComponent.java`

The active helper path delegates from `FBOrderCalculationHelper` to
`SafeFBOrderCalculationHelper`, then uses the `deployment/order` graph engine.
Use this source when diagnosing Studio-side order assignment; verify final
runtime order against generated `vcont.fboot` when behavior matters.

## Data Directory

`data/` contains product assets and domain inputs:

- `data/docs/VC024SA.B Руководство разработчика по VCStudio.pdf`
- `data/docs/VC025SB.A Руководство по инсталляции VCSystem.pdf`
- `data/typelibrary/`: 473 working `.fbt` block type files in the current
  snapshot;
- `data/template/`: templates for `Adapter.adp`, `Basic.fbt`, `Composite.fbt`,
  `ServiceInterface.fbt`, `Simple.fbt`, `SimpleST.fbt`, `Struct.dtp`,
  `SubApp.sub`, etc.;
- `data/st-lua/source_code.st`;
- `data/icons/`;
- `data/keys/`.

Do not store private key values in skill references. Mention only file roles and
paths.

## CI And Release

`.gitlab-ci.yml` includes company templates for Java security, generic rules,
Nexus, Lockbox and SonarQube plus SecObserve upload.

Workflow runs only for `web` pipeline source unless rules are changed.

Main jobs:

- `mvn-test`: `mvn test`, manual.
- `prepare-dependencies`: `mvn dependency:resolve-plugins`, manual.
- `build-artifact-win`: `mvn install ... -Dmaven.test.skip=true
  -Dtycho.disableP2Mirrors=true`, then collects
  `vcstudio*win32*.zip`.
- `build-artifact-linux`: same build, collects `vcstudio*linux*.tar.gz`.
- `sonarqube`: `mvn clean verify sonar:sonar`, tests skipped, allow-failure.
- upload jobs publish snapshot, RC and release artifacts to Nexus repositories:
  `generic-vcont-snapshot`, `generic-vcont-release-candidate`,
  `generic-vcont-release` under `vcont-ide`.
- release path has manual QA/product manager approval jobs for tagged builds.

## Dirty Worktree Notes

This repo can contain many untracked/generated files such as `.polyglot.*`,
generated `pom.tycho` derivatives, copied `MANIFEST.MF` variants and IDE files.
Before editing or staging anything in `vcstudio`, run:

```bash
git status --short --ignored
```

For cross-repo skill refresh work, treat `/home/ant/IdeaProjects/vcstudio` as
read-only unless the user explicitly asks to modify the product repo.
