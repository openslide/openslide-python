---
link-text: Release checklist
repo: openslide/openslide-python
title: Release X.Y.Z
labels: [release]
---

# OpenSlide Python release process

- [ ] Update `CHANGELOG.md` and version in `openslide/_version.py`
- [ ] Create and push signed tag
- [ ] Find the [workflow run](https://github.com/openslide/openslide-python/actions/workflows/python.yml) for the tag
  - [ ] Once the build finishes, approve deployment to PyPI
  - [ ] Download the docs artifact
- [ ] Verify that the workflow created a [PyPI release](https://pypi.org/p/openslide-python) with a description, source tarball, and wheels
- [ ] Verify that the workflow created a [GitHub release](https://github.com/openslide/openslide-python/releases) with release notes, source tarballs, and wheels
- [ ] `cd` into website checkout; `rm -r api/python && unzip /path/to/downloaded/openslide-python-docs.zip && mv openslide-python-docs-* api/python`
- [ ] Update website: `_data/releases.yaml`, `_includes/news.md`
- [ ] Start a [CI build](https://github.com/openslide/openslide.github.io/actions/workflows/retile.yml) of the demo site
- [ ] Update Ubuntu PPA
- [ ] Update Fedora and possibly EPEL packages
- [ ] Check that [Copr package](https://copr.fedorainfracloud.org/coprs/g/openslide/openslide/builds/) built successfully
- [ ] Send mail to -announce and -users
- [ ] Post to [forum.image.sc](https://forum.image.sc/c/announcements/10)
- [ ] Update MacPorts package
