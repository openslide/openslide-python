# Adding a new Python release

- Update Git main
  - [ ] `git checkout main`
  - [ ] In `pyproject.toml`, add classifier for new Python version and update `tool.black.target-version`
  - [ ] Add new Python version to lists in `.github/workflows/python.yml`
  - [ ] Commit and open a PR
  - [ ] Merge the PR when CI passes
  - [ ] Add new Python jobs to [branch protection required checks](https://github.com/openslide/openslide-python/settings/branches)
- [ ] Update MacPorts package
- [ ] Update website: Python 3 versions in `download/index.md`
