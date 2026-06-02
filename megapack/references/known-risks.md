# Megapack Known Risks

These are high-signal risks found from local review of `/home/ant/IdeaProjects/megapack` on 2026-06-02. Re-verify against current files before claiming they still exist.

## Artifact Behavior Risks

### OPC UA selection for licensed install

Observed code risk: `installer/install.sh` selected the VCont deb through `INSTALL_OPCUA`, while `cmd_install()` used local `install_opcua`. If this remains true, `install opcua` for `x86_64/lic` can install the non-OPC UA VCont deb and then fail post-install verification.

Review target:

```bash
shellcheck installer/install.sh
rg -n "INSTALL_OPCUA|install_opcua" installer/install.sh
```

Artifact oracle:

- `x86_64/lic install opcua` must yield `vcont -v` with variant `lic` and OPC UA flag.

### Trial variants and OPC UA

Project docs say `trial-light` and `trial-full` always include OPC UA and install with plain `install`. If the installer only installs OPC UA server packages when the `opcua` argument is passed, trial artifacts can be incomplete.

Artifact oracle:

- `trial-light install` and `trial-full install` must satisfy the agreed OPC UA expectation without requiring `install opcua`, unless product requirements changed.

### Build allows missing OPC UA package directory

Observed source risk: OPC UA-supporting variants may warn and continue if `packages/<arch>/opcua` is missing. That can create a `.run` artifact that claims OPC UA support but fails during install.

Artifact oracle:

- extracted artifact for OPC UA variants must contain expected OPC UA `.deb` files;
- `install` must not discover missing bundled OPC UA files at runtime.

## Repository/CI Risks

### Nexus download URL separator

Observed source risk: `fetch_latest.sh` constructed download URL as `.../repository/${repository}${best_path}`. If Nexus asset `path` does not start with `/`, the URL misses a slash.

Diagnostic:

```bash
FETCH_DEBUG=1 ./scripts/fetch_latest.sh <repo> <pattern> /tmp/out.deb
```

### Stale local package reuse

Observed source risk: `download_deps.sh` skips downloads when destination files already exist. A later run with a new version or new latest artifact can reuse stale `.deb` files under `packages/`.

For release builds, prefer a clean workspace or explicit package cleanup before download.

### Environment variable naming mismatch

The repo snapshot contained CI variables named `REPO_SNAPSHOT`/`REPO_RELEASE`, while scripts used `SNAPSHOT_REPO`/`RELEASE_REPO`. Verify CI templates or job environment before assuming this is harmless.

## Review Severity Guidance

Treat as Critical:

- artifact installs wrong VCont variant;
- `install opcua` produces non-OPC UA runtime;
- trial artifact contradicts product-required OPC UA behavior;
- artifact succeeds but `vcont -v` oracle is wrong.

Treat as Important:

- missing or stale bundled packages;
- misleading dependency diagnostics;
- inconsistent package names in uninstall/purge;
- CI produces artifact names/paths that do not match Nexus contract.

Treat as Minor:

- shell style warnings that do not affect behavior;
- README/TODO formatting issues;
- local help text spacing, unless it misleads field usage.
