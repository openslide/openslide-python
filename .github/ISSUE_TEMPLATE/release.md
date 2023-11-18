# OpenSlide Python release process

- [ ] Update `CHANGELOG.md` and version in `openslide/_version.py`
- [ ] Create and push signed tag
- [ ] `git clean -dxf && mkdir dist`
- [ ] Find the [workflow run](https://github.com/openslide/openslide-python/actions/workflows/python.yml) for the tag; download its dist and docs artifacts
- [ ] `unzip /path/to/downloaded/openslide-python-dist.zip && mv openslide-python-dist-*/* dist/`
- [ ] `twine upload dist/*`
- [ ] Verify that the workflow created a [GitHub release](https://github.com/openslide/openslide-python/releases) with release notes, a source tarball, and wheels
- [ ] `cd` into website checkout; `rm -r api/python && unzip /path/to/downloaded/openslide-python-docs.zip && mv openslide-python-docs-* api/python`
- [ ] Update website: `_data/releases.yaml`, `_includes/news.md`
- [ ] Update Ubuntu PPA
- [ ] Update Fedora and EPEL packages
- [ ] Check that [Copr package](https://copr.fedorainfracloud.org/coprs/g/openslide/openslide/builds/) built successfully
- [ ] Send mail to -announce and -users
- [ ] Post to [forum.image.sc](https://forum.image.sc/c/announcements/10)
- [ ] Update MacPorts package
