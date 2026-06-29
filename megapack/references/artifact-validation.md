# Megapack Artifact Validation

Use this reference when the task is to validate delivered `.run` artifacts only. The source repository scripts are out of scope unless needed to explain a failure.

## Required Inputs

- Exact `.run` artifact path or Nexus URL.
- Expected arch, variant, version, and pipeline id from the filename.
- Target OS baseline, for example Ubuntu 24.04 if that is the supported deployment OS.
- Whether the check is a smoke check, release gate, or regression reproduction.
- Dependency policy:
  - clean OS negative check: missing dependencies should be reported clearly;
  - prepared OS positive check: install should succeed after required system dependencies are installed.

## Recommended Environment

Use one disposable target per scenario.

Preferred:

- VM with snapshot restore.
- Target OS matching customer baseline.
- Root/sudo access.
- Network disabled for the install phase if proving offline behavior.

Acceptable for lightweight smoke:

- Container with enough privileges for `dpkg` checks.
- Only use this if package postinst/service behavior does not require full `systemd`, udev, device access, or production-like networking.

Avoid:

- Running install/purge on the shared workstation.
- Reusing a dirty target without snapshot restore.
- Trusting `purge` as cleanup after a failed install.

## Positive E2E Sequence

Run this on a prepared target with required OS dependencies installed:

```bash
chmod +x ./artifact.run
./artifact.run help
./artifact.run version
sudo ./artifact.run install
/usr/local/sbin/vcont/vcont -v
dpkg -s vcont
sudo ./artifact.run uninstall
sudo ./artifact.run purge
```

For an OPC UA-capable artifact:

```bash
sudo ./artifact.run install opcua
/usr/local/sbin/vcont/vcont -v
dpkg -s vcont
```

For agent coverage:

```bash
sudo ./artifact.run install agent
/usr/local/sbin/vcont/vcont -v
dpkg -s agent-vcmonitor
```

For combined optional features:

```bash
sudo ./artifact.run install opcua agent
/usr/local/sbin/vcont/vcont -v
dpkg -s vcont agent-vcmonitor isource_opcua_server isource_opcua_sb_api
```

Use the real artifact filename in logs, not `artifact.run`.

## Minimum Matrix

| Artifact | Install command | Required oracle |
| --- | --- | --- |
| `x86_64/lic` | `install` | variant `lic`, no OPC UA flag |
| `x86_64/developer` | `install` | variant `developer`, no OPC UA flag |
| each supported `<arch>/<variant>` | `install` | variant matches filename, no OPC UA/agent flag unless expected by current artifact docs |
| representative `<arch>/<variant>` | `install opcua` | variant matches filename, OPC UA packages installed, `vcont -v` reports OPC UA |
| representative `<arch>/<variant>` | `install agent` | variant matches filename, `agent-vcmonitor` installed, `vcont -v` reports agent monitoring when supported |
| representative `<arch>/<variant>` | `install opcua agent` | variant, OPC UA, and agent oracles all match |

Run at least one full optional-feature case per architecture family before claiming the entire release matrix is covered. If product owners change trial/developer OPC UA semantics, update this reference before changing the oracle.

## Negative Scenarios

Run as separate snapshot-isolated cases:

- no root: `./artifact.run install` must fail with a clear root/sudo error;
- missing system dependencies: on clean OS, `install` must list missing dependency names and exit non-zero;
- architecture mismatch: artifact must fail before package install;
- variant conflict: installing `trial-full` over `lic`, or vice versa, must fail before package install;
- OPC UA mismatch: installing without `opcua` over an existing OPC UA install must fail with a clear diagnostic or converge according to documented rules;
- agent mismatch: installing without `agent` over an existing agent-enabled install, or with `agent` over an incompatible state, must fail clearly or converge according to documented rules;
- repeated same-variant install: installing a newer same-variant artifact should update/reinstall without variant conflict.

## Artifact Introspection

Before install, collect:

```bash
sha256sum ./artifact.run
./artifact.run --target /tmp/megapack-extract --noexec
find /tmp/megapack-extract -maxdepth 4 -type f | sort
sed -n '1,200p' /tmp/megapack-extract/metadata.ini
dpkg-deb -f /tmp/megapack-extract/packages/<arch>/*.deb Package Version Depends
test ! -d /tmp/megapack-extract/packages/<arch>/opcua || dpkg-deb -f /tmp/megapack-extract/packages/<arch>/opcua/*.deb Package Version Depends
```

Adjust extraction command if the `makeself` version uses different flags. Keep extracted contents as CI artifacts on failure.

## Pass Criteria

An artifact passes only if:

- `help` and `version` run without crashing;
- `install` exits `0` on a prepared supported target;
- `/usr/local/sbin/vcont/vcont -v` runs;
- installed variant matches the artifact variant;
- OPC UA presence matches the matrix and command;
- agent presence matches the command and package state (`agent-vcmonitor`);
- expected Debian packages are installed according to `dpkg -s`;
- `uninstall` exits `0` and removes package registrations while preserving documented data;
- `purge` exits `0` on a target where packages are installed and removes package-managed state.

Report as failed if install succeeds but the oracle is wrong.

## Diagnostics To Preserve

Always attach or save:

- exact artifact filename and SHA256;
- target OS release: `cat /etc/os-release`;
- architecture: `uname -m`;
- command transcript with exit codes;
- `./artifact.run version` output;
- `vcont -v` output;
- `dpkg -s` for bundled package names;
- installer stdout/stderr;
- `/var/log` or service logs relevant to failed package postinst, if available.
