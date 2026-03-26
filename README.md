# EXiobase-cOmputation-optioNs

A set of python method buildind exiobase as an IOTableBackend in `brightway` and comparing different impacts computations options: 1) direct computations with numpy matrices 2) computations using the regular LCA object from`bw2calc` 3) computions using the `JacobiGMRESLCA` object introduced in `bw2calc v2.4.0`.

## Get started

### Installation

To use a this package, you can clone the repository or download the code. Then create virtual environment to install requirements. Example using ``pip`` and ``venv``:

```sh
py -m venv your_venv_name
./your_venv_name/scripts/activate
pip install --upgrade build
pip install -e .
```

The latter command installs the code of this repo as an *egg* (see [this link](https://setuptools.pypa.io/en/latest/userguide/quickstart.html#development-mode)), which means it will be added to your virtual environment and you'll be able to use it just as any other package. Everything is installed under the name `exon` (EXiobase-cOmputation-optioNs, yes I was lacking inspiration :upside_down_face: ). All dependencies are also installed through this command

Note: I did not separate dev and non dev dependencies so packages like black, mypy and others will also be installed.

### Data needed to run the script

The code uses data from two main sources to run:
#### Exiobase

#### Impact World+
IWP files for exiobase can be downloaded from [Zenodo](https://zenodo.org/records/18892673), latest version to date is 2.2.1 which is the only explicitly supported in `exon`. But code can easily be extended to use other versions (or LCIA method providing CF for exiobase elementary flows are available).

Files (impact_world_plus_2.2.1_expert_version_exiobase_3.8.2_and_before.xlsx ; impact_world_plus_2.2.1_expert_version_exiobase_3.9_and_after.xlsx)

### Usage

To write
