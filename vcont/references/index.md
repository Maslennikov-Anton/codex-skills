# VCont References Index

Open this first when choosing which VCont reference to load.

- `studio-vcont-contract.md`: Studio(front)/VCont(back) lifecycle, ownership boundary, generated artifacts, load/runtime command mapping, HSB boundary.
- `vc024sa-runtime-contract.md`: runtime-facing subset of VC024SA.B: connection, bootfile, task/order semantics, online effects, Modbus/OPC UA blocks and caveats.
- `config.md`: `vcontcfg.json`, runtime DB/state persistence, auth/TLS, HSB settings, diagnostics.
- `runtime-options.md`: `Options="name=value ..."` parameter grammar and defaults for Modbus, EtherNet/IP, KNX, and PROFIBUS runtime devices.
- `protocol.md`: IDE TCP XML commands, auth, `HSBSTATUS`, bootfile signing/validation, FB/task/connection command patterns.
- `bootfile-patterns.md`: minimal `vcont.fboot` skeletons and execution-order guardrails.
- `modbus.md`: VCont Modbus server/client runtime behavior, `HsbAlg`, aliases, async client, RTU-over-TCP, scenario caveats.
- `profibus.md`: Profibus/PRBDEV test infrastructure, PTY slave emulator, closed master-library caveats, and HSB counter journal oracle.
- `hot-standby.md`: HSB roles, `HSBSTATUS`, `GlobalModeManager`, bootfile checksum rules, `HBModeSource`, election, component behavior on role loss.
- `synchronization.md`: peer-to-peer sync model, `SyncManager`, ELET full/partial packets, HSB sync unit, Docker/eCAL notes, failover oracle caveats.
- `logs.md`: VCont log diagnostics and known log patterns.
- `licensing.md`: internal/licensed/trial behavior, license files, trial constraints.
- `test-cases.md`: preserved VCont/HSB test scenarios and expected oracles.
- `hsb-local-commands.md`: local `vcont-hsb` stand commands.

Routing: use VCont references for what actually runs or is observed. For Studio GUI/project workflows, `.vcsys`, UserLibrary, Preferences, monitoring UI, or backup/history, cross over through `studio-vcont-contract.md` to the `vcstudio` skill.
