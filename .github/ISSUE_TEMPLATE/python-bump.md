# Adding wheels for a new Python release

- Update Git main
  - [ ] `git checkout main`
  - [ ] Add classifier for new Python version to `setup.py`
  - [ ] Add new Python version to lists in `.github/workflows/python.yml`
  - [ ] Commit and open a PR
  - [ ] Merge the PR when CI passes
  - [ ] Add new Python jobs to [branch protection required checks](https://github.com/openslide/openslide-python/settings/branches)
- Build new wheels
  - [ ] Check out a new branch from the most recent release tag
  - [ ] Add new Python version to lists in `.github/workflows/python.yml`, commit, and open a DNM PR
  - [ ] Find the [workflow run](https://github.com/openslide/openslide-python/actions) for the PR; download its wheels artifact
  - [ ] Close the PR
- [ ] In OpenSlide Python checkout, `git checkout v<version> && git clean -dxf && mkdir dist`
- [ ] Copy downloaded wheels _from new Python release only_ into `dist` directory
- [ ] `twine upload dist/*`
- [ ] Upload new wheels to [GitHub release](https://github.com/openslide/openslide-python/releases)
- [ ] Update MacPorts package
- [ ] Update website: Python 3 versions in `download/index.md`
