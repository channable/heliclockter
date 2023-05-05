{ buildPythonPackage
, setuptools
, fetchPypi
, isPy311
, isPy310
, isPy39
, isPy38
, isPy37 }:

assert (isPy311 || isPy310 || isPy39 || isPy38 || isPy37);
{
  heliclockter = buildPythonPackage rec {
    format = "pyproject";
    pname = "heliclockter";
    version = "1.0.4";

    propagatedBuildInputs = [
      setuptools
    ];

    src = ../.;
  };
}
