# EXiobase-cOmputation-optioNs

A set of python method buildind exiobase as an IOTableBackend in `brightway` and comparing different impacts computations options: 1) direct computations with numpy matrices 2) computations using the regular LCA object from`bw2calc` with technosphere factorization reuse 3) computions using the `JacobiGMRESLCA` object introduced in `bw2calc v2.4.0`, with and without warm-start guesses.

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

### Quick start - running as `__main__`

You can run the module as `__main__` by running a command in your terminal. Providing you have downloaded relevant data, you can for instance run:
```pwsh
python exon -p exon -d exiobase-3.8.2-2022 -m iwp-2.2.1 -t 1e-3 1e-7 -s all -i 5 -a 10
```
> [!WARNING]
> Exiobase and lcia method data should be downloaded separetly from their respective zenodo nodes for the script to work. See below [Required data](#required-data)

The above command will extract the exiobase 3.8.2 2022 data, build two databases in brightway (one by applying a culling threshold of 1e-3 and a second one applying a culling threshold of 1e-7), import Impact World+ v2.2.1 to brightway, and run computation on 5 randomly selected impact indicators for 10 randomly selected activities. By default, computations will be run for different computation modes:
1) direct matrix iterative -> for each tupple `(indicator, activity)`, the code solves $C.S.((I-A)^{-1}).y$ for a single method in $C$ (the characterization matrix, or vector here) and single activity in $y$ (the demand vector)
2) direct matrix aggregated -> this mode solves $C.S.((I-A)^{-1}).Y$ where all selected methods are in $C$ and $Y$ is a demand matrix containing as many columns as selected activities. Computation time is divided by the number of tupples `(indicator, activity)`
3) `bw2calc.LCA` with reused technosphere factorization and `switch_method()` for repeated LCIA on the same inventory
4) `bw2calc.JacobiGMRESLCA` with `use_guess=False` to benchmark cold starts across repeated right-hand sides
5) `bw2calc.JacobiGMRESLCA` with `use_guess=True` to benchmark warm-start reuse across repeated right-hand sides
6) `bw2calc.MultiLCA`

Get more info about available args by running:
```pwsh
python exon -h
```

### Required Data

The code uses data from two main sources to run:
#### Exiobase
Exiobase archives can be downloaded from [Exiobase Zenodo](https://zenodo.org/records/18937492). Latest version to date is 3.10.1 released in march 2026. Version 3.8.2 is the only version that has been tested in `exon`. The code can easily be extended to use other versions. Brightway computations should run for any version and reference year. Direct matrix computations might fail for other versions due to a variable number of elementary flows that is not accounted for in the characterization matrix for now.

The code works with `pxp` versions of exiobase. Download the `zip` archive and place it in `./data/databases/exiobase/{$version}/IOT_{$ref-year}_pxp.zip` where `$version` & `$ref-year` should correspond to the version downloaded.

> Stadler, K., Wood, R., Bulavskaya, T., Södersten, C.-J., Simas, M., Schmidt, S., Usubiaga, A., Acosta-Fernández, J., Kuenen, J., Bruckner, M., Giljum, S., Lutter, S., Merciai, S., Schmidt, J. H., Theurl, M. C., Plutzar, C., Kastner, T., Eisenmenger, N., Erb, K.-H., … Tukker, A. (2021). EXIOBASE 3 (3.8.2) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.5589597

#### Impact World+
IWP files for exiobase can be downloaded from [IWP Zenodo](https://zenodo.org/records/18892673), latest version to date is 2.2.1 released in march 2026 which is the only explicitly supported in `exon`. The code can easily be extended to use other versions (or LCIA method providing CF for exiobase elementary flows are available).

Files (`impact_world_plus_2.2.1_expert_version_exiobase_3.8.2_and_before.xlsx` ; `impact_world_plus_2.2.1_expert_version_exiobase_3.9_and_after.xlsx`) should be placed in `./data/lcia_methods/iwp/2.2.1`.

> Agez, M., Muller, E., Greffe, T., Loog, K., Bulle, C., Saadi, N., & Boulay, A.-M. (2026). IMPACT World+ / a globally regionalized method for life cycle impact assessment (2.2) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.18200775

### Using package methods in a notebook
Alternatively all relevant methods can be used on their own in notebook by importing them from the package. See tutorial notebook [To Add].
