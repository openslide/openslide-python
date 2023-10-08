# OpenSlide Python release process

- [ ] Update `CHANGELOG.md` and version in `openslide/_version.py`
- [ ] Create and push signed tag
- [ ] `git clean -dxf && mkdir dist`
- [ ] Find the [workflow run](https://github.com/openslide/openslide-python/actions) for the tag; download its docs and wheels artifacts
- [ ] `unzip /path/to/downloaded/openslide-python-wheels.zip && mv openslide-python-wheels-*/* dist/`
- [ ] `python setup.py sdist`
- [ ] `twine upload dist/*`
- [ ] Recompress tarball with `xz`
- [ ] Attach release notes to [GitHub release](https://github.com/openslide/openslide-python/releases/new); upload tarballs and wheels
- [ ] `cd` into website checkout; `rm -r api/python && unzip /path/to/downloaded/openslide-python-docs.zip && mv openslide-python-docs-* api/python`
- [ ] Update website: `_data/releases.yaml`, `_includes/news.md`
- [ ] Update Ubuntu PPA
- [ ] Send mail to -announce and -users
- [ ] Update Fedora and EPEL packages
- [ ] Update MacPorts package
