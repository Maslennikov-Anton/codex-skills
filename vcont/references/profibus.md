# Profibus / PRBDEV

Use this reference for VCont tasks involving Profibus DPV0, `PRBDEV`, local
Profibus emulators, or HSB tests where the external fieldbus endpoint is the
oracle.

## Local `vcont-hsb` emulator pattern

In `/home/ant/IdeaProjects/vcont-hsb`, the Profibus work uses a standalone
slave emulator under `docker/profibus`:

- `profibus_slave_emulator.c`: DPV0 slave emulator over serial/TTY.
- `VC_GSD.gsd`: device GSD used for ident and buffer sizes.
- `profibus_smoke_test.py`: PTY-based smoke without hardware.
- `Makefile`: `profibus_slave_emulator`, `smoke`, and optional demo master
  build targets.

For CI-style checks, prefer PTY over physical RS-485 unless the task explicitly
requires hardware timing. PTY verifies frame parsing, service dispatch, state
recording, and test oracles, but it does not prove USB-RS485 latency or TSDR on
a real Profibus line.

## Closed master library caveat

`librtprofibus.a`, `demo2.c`, XML configs, and the vendor headers may be useful
as integration references, but do not make deterministic CI tests depend on the
closed master library by default. In the local PTY attempt, the library returned
`RTPB_ERR_NOT_READY`; without source code, root-causing that path is speculative.

If the user says the supplied library/XML/demo files are "for example", keep
them as reference inputs and implement the reproducible test layer around the
emulator/protocol behavior instead.

## DPV0 services to cover

A basic emulator/test path should initialize the slave before cyclic exchange:

1. `Set_Prm`
2. `Set_Cfg`
3. `Get_Diag`
4. repeated `Data_Exchange`

For the current `vcont-hsb` test, `Set_Prm` and `Set_Cfg` acknowledge with
`E5`; `Get_Diag` returns an SD2 diagnostic response; `Data_Exchange` returns an
SD2 input-data response and records the master's output payload.

## HSB counter journal oracle

For HSB-style fieldbus continuity, use the external endpoint's journal as the
primary oracle. The current Profibus test case records each `Data_Exchange`
sample with:

- `sequence`
- `timestamp`
- `delta_ms`
- `counter`
- `output_len`
- `output_hex`

The counter is read from the first two output bytes as little-endian `uint16`.
If the real Profibus map places the counter at another offset, parameterize the
offset instead of changing the continuity assertion.

Expected assertions for the base testcase:

- initialization services were handled at least once;
- `Data_Exchange` count is at least the number of expected samples;
- counter values are continuous with step `+1`;
- every sample after the first has `delta_ms`;
- with a 50 ms main task, every `delta_ms` is less than 1000 ms;
- raw state, JSONL journal, CSV journal, and evidence JSON are attached to
  Allure.

## Simulating takeover

When VCont/PRBDEV is not part of the deterministic test yet, simulate MAIN
takeover by switching the master source address while continuing the same
counter sequence. In the local testcase this is `master_id 2 -> 3`, with
8 samples before takeover and 12 after takeover.

Treat this as a transport/oracle test, not proof of real VCont HSB election.
For a full integration test, add a separate layer where VCont `PRBDEV` or real
Profibus hardware drives the same journal oracle.

## Useful review artifacts

For review reports in `vcont-hsb/reports`, document:

- infrastructure and files used;
- exact test steps;
- expected result and actual result;
- why `librtprofibus.a` is or is not part of the runtime path;
- artifacts attached to Allure;
- limitations: PTY vs RS-485, simulated source-address takeover, closed vendor
  library, and counter offset assumptions.
