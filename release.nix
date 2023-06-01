{ version, pkgs ? import ./nix/nixpkgs-pinned.nix { } }:
{
  heliclockter = pkgs.pythonChannable.pkgs.callPackage ./nix/heliclockter.nix { };
}
