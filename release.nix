{ version }:
let
  package = import ./nix/package.nix { inherit version; };
in {
  heliclockter = package.package;
}
