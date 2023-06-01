{ environment ? "default"
}:
let
    pkgs = import ./nix/nixpkgs-pinned.nix {};

    python = pkgs.pythonChannable;

    pythonEnv = python.withPackages (p: [
      heliclockter
      p.bandit
      p.black
      p.mypy
      p.pydantic
      p.pylint
      p.pytest
      p.toml
      p.tkinter
      p.testscenarios
      p.testresources
      p.fixtures
      p.distutils_extra
    ]);

    # Environment in use by default when running commands via `nix shell`.
    # This can also be used on CI to run tests and style checks.
    defaultEnv = pkgs.buildEnv {
      name = "heliclockter-env-default";
      paths = with pkgs; [
          # Python dependencies
          pythonEnv

          # Manage nix pins
          niv
          nvd
      ];
    };

    heliclockter = pkgs.pythonChannable.pkgs.callPackage ./nix/heliclockter.nix { };

    # Lookup for the environments defined in this file. This is used below
    # to allow the user to override which set of dependencies to use.
    environments = {
        default = defaultEnv;
        package = heliclockter;
        dev-python-env = pythonEnv;
        shell = pkgs.mkShell { packages = [defaultEnv]; };
    };
in
    # Allow users to choose an environment by supplying a value for the
    # `environment` argument to this file. Error out if the environment is not
    # defined in the `environments` attrset.
    environments."${environment}" or (throw ''
        Unknown environment: ${environment}

        You are probably getting this error because you attempted to run a
        command using `nix shell` like so:

            nix shell --file default.nix --argstr environment ${environment} -c foo

        However, the value `${environment}` is not supported. You can choose from:

          - ${builtins.concatStringsSep "\n - " (builtins.attrNames environments)}'')
