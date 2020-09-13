# Adding wheels for a new Python release

- [ ] [Add two new build matrix groups](https://ci.appveyor.com/project/OpenSlide/openslide-python/settings/environment) to AppVeyor job with appropriate PYTHON variables
- [ ] [Select the original OpenSlide Python release build](https://ci.appveyor.com/project/OpenSlide/openslide-python/history) in AppVeyor, then click "Rebuild Commit"
- [ ] In OpenSlide Python checkout, `git checkout v<version> && git clean -dxf && mkdir dist`
- [ ] Download wheels _from new build jobs only_ into `dist` directory
- [ ] `twine upload dist/*`
- [ ] Upload new wheels to [GitHub release](https://github.com/openslide/openslide-python/releases)
- [ ] [Download new AppVeyor YAML](https://ci.appveyor.com/project/OpenSlide/openslide-python/settings/yaml) and commit it to `openslide-automation/appveyor/openslide-python.yml`
- [ ] Update MacPorts package
- [ ] Update website: Python 3 versions in `download/index.md`
