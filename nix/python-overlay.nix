{ sources ? import ./sources.nix }:
# Returns an overlay which adds missing Python dependencies to Nixpkgs.
# Is applied to a Python package set e.g. pkgs.python310 / pkgs.pythonChannable.

self: super: {
  heliclockter = self.callPackage ./heliclockter.nix { };
}
