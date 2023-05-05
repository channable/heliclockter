# Helper file to be able to access intermediate Nix derivations once added

{ version, pkgs ? import ./nixpkgs-pinned.nix { } }:
rec {
  package = pkgs.pythonChannable.pkgs.callPackage ./heliclockter.nix { };
}
