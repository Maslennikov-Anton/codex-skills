# Megapack Project Model

## Purpose

Megapack packages VCont and required dependencies into offline self-extracting `.run` installers for customer-site deployment. The intended user is a field engineer or non-developer operator with a USB drive and no internet access on the target site.

The project path is `/home/ant/IdeaProjects/megapack`.

## Artifact Naming

Format:

```text
vcont-<arch>-<variant>-<version>-<pipeline_id>.run
```

Nexus path:

```text
<repo>/vcont-runtime/megapack/<arch>/<variant>/vcont-<arch>-<variant>-<version>-<pipeline_id>.run
```

Snapshot repository is normally `generic-vcont-snapshot`. Release repository is normally `generic-vcont-release`.

## Matrix

| Architecture | Variant | OPC UA expectation | VCont debs inside |
| --- | --- | --- | --- |
| `x86_64` | `lic` | optional via `install opcua` | both OPC UA and non-OPC UA licensed debs |
| `x86_64` | `trial-light` | always expected | one OPC UA trial-light deb |
| `x86_64` | `trial-full` | always expected | one OPC UA trial-full deb |
| `x86_64` | `developer` | no | one developer deb |
| `x86_64-legacy` | `lic` | no | one legacy licensed deb |
| `x86_64-legacy` | `developer` | no | one legacy developer deb |

`aarch64` and `aarch64-legacy` are future work and currently blocked by missing ARM eCAL wheel support in the known project notes.

## Bundled Components

Expected package categories:

- `vcont`: one or two `.deb` depending on variant.
- `configurator`: `.deb`, chosen as latest snapshot.
- `agent`: `.deb`, chosen as latest snapshot; eCAL wheel handling is expected inside agent package.
- `ecal`: `.deb`, fixed release package under `vcont-runtime/vcont-libraries/<arch>/ecal.deb`.
- `opcua`: server/API `.deb` packages for OPC UA variants.

## Installer Commands

The `.run` artifact exposes:

```bash
sudo ./artifact.run help
sudo ./artifact.run version
sudo ./artifact.run install
sudo ./artifact.run install opcua
sudo ./artifact.run uninstall
sudo ./artifact.run purge
```

Expected install order:

1. Check root.
2. Check architecture.
3. Check system dependencies extracted from bundled `.deb` `Depends`, plus `pip3`.
4. Check installed VCont variant and OPC UA conflict through `/usr/local/sbin/vcont/vcont -v`.
5. Install `ecal`.
6. Install OPC UA packages if selected/required.
7. Install `agent`.
8. Install `configurator`.
9. Install selected `vcont` package.
10. Verify `vcont -v`.

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
