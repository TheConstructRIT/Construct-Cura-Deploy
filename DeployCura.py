"""
Zachary Cook

Deploys Cura with the settings and modifications used by The Construct @ RIT.
"""

import ctypes
import json
import os
import shutil
import sys
import re
import requests
import zipfile
from typing import Optional
from Configuration import KNOWN_CURA_LOCATIONS, SERVER_HOST


def downloadArchive(url, name) -> None:
    """Downloads and extracts an archive.

    :param url: URL to download from.
    :param name: Name of the file to create
    """

    # Download the file.
    downloadFolder = os.path.join(__file__, "..", "download")
    if not os.path.exists(downloadFolder):
        os.makedirs(downloadFolder)
    downloadFile = os.path.join(downloadFolder, name + ".zip")
    if not os.path.exists(downloadFile):
        with open(downloadFile, "wb") as file:
            file.write(requests.get(url).content)

    # Extract the archive.
    extractFile = os.path.join(downloadFolder, name)
    if not os.path.exists(extractFile):
        os.makedirs(extractFile)
        with zipfile.ZipFile(downloadFile, "r") as zipFile:
            zipFile.extractall(extractFile)


def patchCura() -> None:
    """Patches the Cura files. Runs the script as admin.
    """

    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, "PatchCura.py", None, 1)


def getLatestCuraVersion() -> (Optional[str], Optional[int]):
    # Iterate over the installs to find the latest version.
    latestFullVersion = None
    latestMinorVersion = None
    for knownParent in KNOWN_CURA_LOCATIONS:
        if os.path.isdir(knownParent):
            for curaDirectory in os.listdir(knownParent):
                if "ultimaker cura" in curaDirectory.lower():
                    versionParts = re.findall(r"\d+", curaDirectory)
                    minorVersion = float(versionParts[0] + "." + versionParts[1])
                    if latestMinorVersion is None or minorVersion > latestMinorVersion:
                        latestMinorVersion = minorVersion
                        latestFullVersion = ".".join(versionParts)

    # Return the latest full and minor versions.
    return latestFullVersion, latestMinorVersion


def deploySettings() -> None:
    """Deploys the user settings for Construct Cura.
    """

    # Get the latest installed version.
    latestFullVersion, latestMinorVersion = getLatestCuraVersion()
    if latestFullVersion is None:
        raise Exception("Failed to detect an install of Cura.")

    # Clear the existing settings.
    curaSettingsDirectory = os.path.join(os.getenv("APPDATA"), "cura")
    if not os.path.isdir(curaSettingsDirectory):
        os.makedirs(curaSettingsDirectory)
    for file in os.listdir(curaSettingsDirectory):
        path = os.path.join(curaSettingsDirectory, file)
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)

    # Copy the settings.
    sourceSettings = os.path.join(__file__, "..", "StaticConfiguration")
    targetSettings = os.path.join(os.getenv("APPDATA"), "cura", str(latestMinorVersion))
    shutil.copytree(sourceSettings, targetSettings)

    # Set the last used version to hide the changelog.
    # Due to the sandbox settings, this would get shown every time.
    configurationFile = os.path.join(targetSettings, "cura.cfg")
    configurationFileLines = []
    with open(configurationFile) as file:
        for line in file.readlines():
            if line.strip().startswith("last_run_version"):
                line = line.replace(re.findall(r"[\d.]+", line)[0], latestFullVersion)
            configurationFileLines.append(line)
    with open(configurationFile, "w") as file:
        file.writelines(configurationFileLines)

    # Download and copy the X3G plugin.
    downloadArchive("https://github.com/Ghostkeeper/X3GWriter/releases/download/v1.1.12/X3GWriter7.0.0.curapackage", "X3GWriter")
    pluginsPath = os.path.join(targetSettings, "plugins")
    shutil.copytree(os.path.join(__file__, "..", "download", "X3GWriter", "files", "plugins", "X3GWriter"), os.path.join(pluginsPath, "X3GWriter"))

    # Download and copy the Construct plugins.
    downloadArchive("https://github.com/TheConstructRIT/Construct-Cura-Plugins/archive/refs/heads/master.zip", "Construct-Plugins")
    constructPluginsParentDirectory = os.path.join(__file__, "..", "download", "Construct-Plugins", "Construct-Cura-Plugins-master")
    for pluginName in os.listdir(constructPluginsParentDirectory):
        pluginPath = os.path.join(constructPluginsParentDirectory, pluginName)
        if os.path.isdir(pluginPath):
            shutil.copytree(pluginPath, os.path.join(pluginsPath, pluginName))

    # Set the environment file to the main server.
    environmentFile = os.path.join(pluginsPath, "ConstructCore", "environment.json")
    with open(environmentFile) as file:
        environment = json.loads(file.read())
    environment["SERVER_HOST"] = SERVER_HOST
    with open(environmentFile, "w") as file:
        file.write(json.dumps(environment, indent=4))


if __name__ == '__main__':
    patchCura()
    deploySettings()