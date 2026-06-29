# Megapack Project Model

## Purpose

Megapack packages VCont and required dependencies into offline self-extracting `.run` installers for customer-site deployment. The intended user is a field engineer or non-developer operator with a USB drive and no internet access on the target site.

The project path is `/home/ant/IdeaProjects/megapack`.

## Artifact Naming And Release Path

Format:

```text
vcont-<arch>-<variant>-<version>-<pipeline_id>.run
```

Nexus path:

```text
<repo>/vcont-runtime/megapack/<arch>/<variant>/vcont-<arch>-<variant>-<version>-<pipeline_id>.run
```

Snapshot repository is normally `generic-vcont-snapshot`. Release repository is normally `generic-vcont-release`.

Release CI uploads to:

```text
generic-vcont-release/vcont-runtime/megapack/<arch>/<variant>/vcont-<arch>-<variant>-<version>-<pipeline_id>.run
```

## Matrix

| Architecture | Variants | Filename pattern |
| --- | --- | --- |
| `x86_64` | `developer`, `lic`, `trial-light`, `trial-full` | `vcont-x86_64-<variant>-<version>-<pipeline_id>.run` |
| `x86_64-legacy` | `developer`, `lic`, `trial-light`, `trial-full` | `vcont-x86_64-legacy-<variant>-<version>-<pipeline_id>.run` |
| `aarch64` | `developer`, `lic`, `trial-light`, `trial-full` | `vcont-aarch64-<variant>-<version>-<pipeline_id>.run` |
| `aarch64-legacy` | `developer`, `lic`, `trial-light`, `trial-full` | `vcont-aarch64-legacy-<variant>-<version>-<pipeline_id>.run` |

Current developer README presents OPC UA and agent as install-time options, not variant-implied defaults. Validate the artifact command actually used: plain `install`, `install opcua`, `install agent`, or `install opcua agent`.

## Bundled Components

Expected package categories:

- `vcont`: non-OPC UA and OPC UA `.deb` variants where available.
- `configurator`: `.deb`.
- `agent`: `.deb`, package name `agent-vcmonitor`.
- `ecal`: `.deb`.
- `opcua`: `isource_opcua_server` and `isource_opcua_sb_api` packages.

Important package-name mapping:

| Deb file | Debian package |
| --- | --- |
| `vcont.lin.{arch}.deb` and variant/opcua forms | `vcont` |
| `configurator.deb` | `configurator` |
| `agent.deb` | `agent-vcmonitor` |
| `ecal.deb` | `ecal` |
| `isource_opcua-SERVER.deb` | `isource_opcua_server` |
| `isource_opcua-SB_API.deb` | `isource_opcua_sb_api` |

## Installer Commands

The `.run` artifact exposes:

```bash
sudo ./artifact.run help
sudo ./artifact.run version
sudo ./artifact.run install
sudo ./artifact.run install opcua
sudo ./artifact.run install agent
sudo ./artifact.run install opcua agent
sudo ./artifact.run uninstall
sudo ./artifact.run purge
```

If `/tmp` is mounted `noexec`, run with an executable extraction directory:

```bash
sudo TMPDIR=/var/tmp ./artifact.run install
```

Expected install order:

1. Check root.
2. Load `metadata.ini`.
3. Detect OS: Ubuntu 22.04/24.04 and Debian 11/12 are supported; Pop!_OS, Astra Linux, RedOS, RHEL/CentOS/Fedora/Rocky/AlmaLinux are warnings; other OS families are errors.
4. Check system dependencies extracted from bundled `.deb` `Depends`, plus `pip3`.
5. Check installed VCont variant, OPC UA, and agent conflicts through `/usr/local/sbin/vcont/vcont -v`.
6. Run `dpkg --dry-run -i` preflight for all selected `.deb` files.
7. Install `ecal`.
8. Install OPC UA packages if the `opcua` flag is selected.
9. Install `agent` if the `agent` flag is selected.
10. Install `configurator`.
11. Install selected `vcont` package.
12. Verify `vcont -v`, variant, OPC UA, and agent state.

`uninstall` removes packages while preserving data. `purge` removes packages and package-managed config/data.

## VCont Version Oracle

The expected `vcont -v` shape in project notes is:

```text
vcont v.1.1.0.0 2026-05-26 11:40:54 lic, opcua, agent monitoring
```

Use it to extract:

- variant: `lic`, `trial-light`, `trial-full`, or `developer`;
- flags: `opcua`, `agent monitoring`, etc.

Do not rely only on a substring check when a strict release claim matters. Parse the variant and flags explicitly in the validation harness.
