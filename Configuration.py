"""
Zachary Cook

Common configuration for the deployment.
"""

# Known locations for the Cura installs.
KNOWN_CURA_LOCATIONS = ["C:/Program Files/"]

# Host for the server.
SERVER_HOST = "https://hack.rit.edu:7000"

# Printers that are allowed to be used.
WHITELISTED_PRINTER_DEFINITIONS = {
    # Abstract
    "fdmextruder.def.json",
    "fdmprinter.def.json",
    "artillery_base.def.json",

    # Printers
    "prusa_i3_mk3.def.json",
    "flashforgecreatorpro.def.json",
    "artillery_sidewinder_x1.def.json",
}

# Modifications made to the printer profiles.
PRINTER_OVERRIDES = {
    "prusa_i3_mk3.def.json": {
        "adhesion_type": { "default_value": "brim" },
        "support_enable": { "default_value": True },
        "infill_sparse_density": { "default_value": 15 },
        "raft_margin": { "default_value": 5 },
    },
    "artillery_base.def.json": {
        "adhesion_type": { "default_value": "raft" },
        "support_enable": { "default_value": True },
        "infill_sparse_density": { "default_value": 15 },
        "raft_margin": { "default_value": 5 },
        "support_infill_rate": { "value": "0 if support_enable and support_structure == 'tree' else 15" },
        "support_use_towers": { "value": True },
        "support_wall_count": { "value": 0 },
        "support_brim_enable": { "value": False },
    },
}