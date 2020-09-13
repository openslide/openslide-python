# OpenSlide Python release process

- [ ] Update `CHANGELOG.txt` and version in `openslide/_version.py`
- [ ] Create and push signed tag
- [ ] [Launch AppVeyor build](https://ci.appveyor.com/project/OpenSlide/openslide-python)
- [ ] `git clean -dxf && mkdir dist`
- [ ] Download wheels from each build job into `dist` directory
- [ ] `python setup.py register sdist`
- [ ] `twine upload dist/*`
- [ ] Recompress tarball with `xz`
- [ ] Attach release notes to [GitHub release](https://github.com/openslide/openslide-python/releases/new); upload tarballs and wheels
- [ ] `python setup.py build_sphinx` and copy `build/sphinx/html/` to website `api/python/`
- [ ] Update website: `_data/releases.yaml`, `_includes/news.md`
- [ ] Send mail to -announce and -users
- [ ] Update Fedora package
- [ ] Update MacPorts package
