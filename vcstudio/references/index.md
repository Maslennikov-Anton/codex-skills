# VCStudio References Index

Open this first when choosing which VCStudio reference to load.

- `studio-vcont-contract.md`: Studio(front)/VCont(back) lifecycle, ownership boundary, object mapping, load/runtime command mapping, HSB boundary.
- `vc024sa-key-facts.md`: compact complete facts from the current VC024SA.B Studio manual PDF for most Studio questions.
- `vc024sa-section-map.md`: navigation map for the full extracted VC024SA.B text; prefer it over the PDF TOC for sections `6.7+`, where the TOC is stale.
- `vc024sa-complete.md`: full embedded text extracted from `Руководство_правки_июнь.pdf` for exact wording, rare table rows, figure captions, and typo-sensitive details.
- `project-workflow.md`: project/workspace, device/resource/application/loop hierarchy, tasks, FBs, connections, order, event-loop authoring.
- `st-language.md`: Studio ST emulation rules: editor grammar vs bundled translator grammar, wrapper paths, interfaceSpec/index/codegen rules, and ST loop vs user ST FB behavior.
- `loading-monitoring.md`: load command streams, ST/Lua instance creation, TCP/TLS framing, Watch monitoring, live writes, forcing, and manual event trigger protocol.
- `communications.md`: Studio-side Modbus/OPC UA setup, runtime `Options` mirror, and generated artifact mapping.
- `fb-typelibrary.md`: verified local VCStudio FB typelibrary shape, `.fbt` format, source counts, runtime mapping, guardrails, and high-value communication blocks.
- `fb-typelibrary-catalog.md`: full generated snapshot of all 473 `.fbt` block interfaces from `/home/ant/IdeaProjects/vcstudio/data/typelibrary`; search with `rg` by block name before opening because it is large.
- `source-repo-map.md`: verified local VCStudio source repo map: Tycho build, product packaging, plugins/features/tests, custom `ru.isource.*` bundles, EMF model, DTO/JSON layer, CI/release, dirty-worktree notes.

Routing: use VCStudio references for how to model/configure/click/edit. For actual runtime execution, logs, bootfile diagnostics, HSB behavior, or test oracles, cross over through `studio-vcont-contract.md` to the `vcont` skill.
