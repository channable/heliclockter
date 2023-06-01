self: super:
let
  sources = import ./sources.nix;
  pythonOverlay = import ./python-overlay.nix {
    inherit sources;
  };
in
{
  sources = if super ? sources then super.sources // sources else sources;

  pythonChannableOverlay = self.lib.composeManyExtensions [ pythonOverlay ];

  # The explicit choice is made not to override `python310`, as this will cause a rebuild of many
  # packages when nixpkgs uses python 3.10 as default python environment.
  # These packages should not be affected, e.g. cachix. This is because of a transitive
  # dependency on the Python packages that we override.
  # In our case cachix > ghc > shpinx > Python libraries.
  pythonChannable = super.python310.override { packageOverrides = self.pythonChannableOverlay; };
}
