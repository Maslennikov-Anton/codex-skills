---
name: megapack
description: "Validate VCont Megapack .run artifacts and inspect /home/ant/IdeaProjects/megapack: installer behavior, package matrix, Nexus paths, artifact-only checks, install/uninstall/purge risks."
---

# Megapack

Use this skill for VCont Megapack work: ready `.run` artifacts, their install behavior, artifact validation plans, Nexus naming, package matrix, or project-specific review of `/home/ant/IdeaProjects/megapack`.

## Workflow

1. Decide the task scope:
   - artifact validation or customer-delivery readiness -> read `references/artifact-validation.md` first;
   - project purpose, matrix, naming, package contents -> read `references/project-model.md`;
   - repository scripts, CI, Nexus download/build/upload flow -> read `references/repository-workflow.md`;
   - review, debugging, or suspicious behavior -> read `references/known-risks.md`.
2. If the user says they only care about delivered artifacts, do not propose unit tests for repository scripts. Validate the `.run` on a clean target VM/container and treat repository code only as diagnostic context.
3. Prefer VM snapshots for real VCont packages. Use Docker only for lightweight artifact smoke checks when package postinst/service behavior does not require full `systemd`, udev, privileged device access, or production-like networking.
4. Treat `README.md` and `TODO.md` in the repo as useful but not authoritative when they conflict with executable scripts or actual `.run` behavior.
5. For VCont runtime semantics, licensing, trial behavior, boot files, logs, or HSB behavior, combine with the `vcont` skill. Keep Megapack-specific decisions here: package composition, installer commands, artifact matrix, and validation oracle.
6. Before claiming an artifact is installable or release-ready, use `verification-before-completion`: provide the exact artifact, environment, command sequence, exit codes, and post-install evidence.

## Core Model

- Megapack creates self-extracting `makeself` `.run` installers for offline VCont deployment on customer hardware.
- The delivered artifact bundles Debian packages and `installer/install.sh`; it supports `help`, `version`, `install [opcua]`, `uninstall`, and `purge`.
- The main supported matrix is `x86_64` developer/lic/trial-light/trial-full plus `x86_64-legacy` developer/lic.
- The field-use goal is one command on the target host: `sudo ./vcont-<arch>-<variant>-<version>-<pipeline_id>.run install [opcua]`.
- Artifact validation should prove the delivered `.run`, not just the source repository scripts.

## Guardrails

- Do not run `install`, `uninstall`, or `purge` on the shared workstation unless the user explicitly asks and accepts system mutation. Use disposable targets.
- Do not rely on `purge` as the only cleanup between test cases; restore a VM snapshot when possible.
- Do not assume "latest" Nexus artifacts are stable. Record concrete `.run` filename, version, pipeline id, SHA256, target OS, and install command.
- Do not weaken artifact checks to make a broken artifact pass. If `install` succeeds but variant, OPC UA flag, packages, or `vcont -v` are wrong, report failure.
