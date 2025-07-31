locals {
  base_path = abspath("${path.root}/../lambda")
  build_script = abspath("${path.root}/../lambda/build-package.sh")
}
