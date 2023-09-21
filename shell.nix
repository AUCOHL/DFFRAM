# Copyright 2023 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
{
    pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/0218941ea68b4c625533bead7bbb94ccce52dceb.tar.gz") {}
}:

let openlane-src = pkgs.fetchFromGitHub {
    owner = "efabless";
    repo = "openlane2";
    rev = "0c05b7ea04eac74203a9a33f8a8b519f33220f2f";
    sha256 = "sha256-fjYz6HuIYrGbkb1oA6wPIlEjieYU5hu0aygYQFj2d2I=";
}; in import "${openlane-src}/shell.nix" {}