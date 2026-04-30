EXIOBASE_MEURO = "M.EUR"
EURO_UNIT = "euro"
BW_REFERENCE_FLOW_TYPE = "production"
BW_PROCESS_TYPE = "process"
EXIOBASE_CULLING_THRESHOLD = 1e-15
CONDITIONS_FOR_EXIOBASE_BIOSPHERE = [
    # (condition, type, categories)
    (lambda s: " - air" in s, "emission", ("air",)),
    (lambda s: " - water" in s, "emission", ("water",)),
    (lambda s: " - soil" in s, "emission", ("soil",)),
    (
        lambda s: any(
            x in s
            for x in [
                "Cropland",
                "Forest area",
                "Other land Use",
                "Permanent pastures",
                "Infrastructure land",
            ]
        ),
        "natural resource",
        ("natural resource", "land"),
    ),
    (
        lambda s: "Extraction" in s
        and any(
            x in s
            for x in [
                "Crop residues",
                "Fishery",
                "Fodder crops",
                "Forestry",
                "Grazing",
                "Primary Crops",
            ]
        ),
        "natural resource",
        ("natural resource", "biotic"),
    ),
    (
        lambda s: "Extraction" in s
        and any(x in s for x in ["Fossil Fuel", "Metal Ores", "Non-Metallic Minerals"]),
        "natural resource",
        ("natural resource", "in ground"),
    ),
    (lambda s: "Water " in s, "natural resource", ("natural resource", "in water")),
    (
        lambda s: "Energy " in s,
        "inventory indicator",
        ("inventory indicator", "resource use"),
    ),
    (
        lambda s: s == "Emissions nec - waste - undef",
        "inventory indicator",
        ("inventory indicator", "waste"),
    ),
    (
        lambda s: any(
            x in s for x in ["axes", "wages", "Operating surplus", "Employment"]
        ),
        "economic",
        ("economic", "primary production factor"),
    ),
]
