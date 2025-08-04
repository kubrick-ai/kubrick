locals {
  base_path    = abspath("${path.root}/../lambda/src")
  build_script = abspath("${path.root}/../lambda/build-package.sh")
}
