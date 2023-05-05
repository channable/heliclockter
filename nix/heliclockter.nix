{ buildPythonPackage
# , setuptools
, fetchPypi
, pythonOlder
}:

{
  heliclockter = buildPythonPackage rec {
    format = "pyproject";
    pname = "heliclockter";
    version = "1.0.4";

    disabled = pythonOlder "3.7";

    # propagatedBuildInputs = [
    #   setuptools
    # ];

    src = ../.;
  };
}
