{ buildPythonPackage
, setuptools
, pytest
, fetchPypi
, pythonOlder
}:

buildPythonPackage {
    format = "pyproject";
    pname = "heliclockter";
    version = "1.0.4";

    disabled = pythonOlder "3.7";

    checkInputs = [ pytest ];

    propagatedBuildInputs = [
      setuptools
    ];

    src = ../.;
}
