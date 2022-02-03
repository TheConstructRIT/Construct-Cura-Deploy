# Construct Cura Deploy
Helper scripts for deploying the plugins and profile
changes for The Construct @ RIT. The changes include:
- Patching the Cura plugins with changes that have not been merged.
- Adding and modifying printer profiles.
- Removing printer profiles that The Construct @ RIT doesn't use.
- Deploying a static configuration for Ultimaker Cura with plugins.

## Running
The system running Ultimaker Cura needs to have Python 3 installed
with the `requests` library installed. On Windows, this can be done
with the following is Python is in the user or system PATH.
```bash
python -m pip install requests
```

After it is installed, the `DeployCura.py` can be called using a
**non-admin** command prompt or terminal.
```bash
python DeployCura.py
```

If a User Access Control (UAC) prompt does not appear, that means
the patching to Cura was not done. In an **admin** command prompt,
the following will need to be run:
```bash
python PatchCura.py
```