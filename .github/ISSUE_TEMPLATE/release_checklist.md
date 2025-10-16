---
name: Release checklist
about: Checklist to publish a new release
title: "[Release] vX.Y.Z"
labels: release
assignees: ''
---

## Prepare
- [ ] Update CHANGELOG.md with highlights
- [ ] Draft notes under Releases/vX.Y.Z-notes.md (or docs/releases/)
- [ ] Verify installer assets built under electron/out/make

## Publish
- [ ] Create GitHub release with tag vX.Y.Z
- [ ] Upload assets (Setup.exe, .nupkg, RELEASES, ZIP)
- [ ] Link to full notes (docs/releases or Releases/)

## Verify
- [ ] Download links resolve in README
- [ ] Actions badge shows green for snake workflow
- [ ] Basic smoke test on Windows 10/11