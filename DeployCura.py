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
from typing import Optional, Tuple
from Configuration import KNOWN_CURA_LOCATIONS, SERVER_HOST, PRINTER_OVERRIDES, MATERIAL_OVERRIDES


def downloadArchive(url: str, name: str) -> None:
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


def getLatestCuraVersion() -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """Gets the latest installed Cura version.

    :return: The directory of the install, the full version of the install, and the minor version of the install.
    """

    # Iterate over the installs to find the latest version.
    latestCuraDirectory = None
    latestFullVersion = None
    latestMinorVersion = None
    for knownParent in KNOWN_CURA_LOCATIONS:
        if os.path.isdir(knownParent):
            for curaDirectory in os.listdir(knownParent):
                if "ultimaker cura" in curaDirectory.lower():
                    versionParts = re.findall(r"\d+", curaDirectory)
                    minorVersion = float(versionParts[0] + "." + versionParts[1])
                    if latestMinorVersion is None or minorVersion > latestMinorVersion:
                        latestCuraDirectory = os.path.join(knownParent, curaDirectory)
                        latestMinorVersion = minorVersion
                        latestFullVersion = ".".join(versionParts)

    # Return the latest full and minor versions.
    return latestCuraDirectory, latestFullVersion, latestMinorVersion


def deploySettings() -> None:
    """Deploys the user settings for Construct Cura.
    """

    # Get the latest installed version.
    latestCuraDirectory, latestFullVersion, latestMinorVersion = getLatestCuraVersion()
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

    # Copy and modify the printers.
    settingsDefinitionsDirectory = os.path.join(targetSettings, "definitions")
    globalDefinitionsDirectory = os.path.join(latestCuraDirectory,"share","cura","resources", "definitions")
    if not os.path.exists(settingsDefinitionsDirectory):
        os.makedirs(settingsDefinitionsDirectory)
    for fileName in PRINTER_OVERRIDES.keys():
        if fileName in PRINTER_OVERRIDES.keys():
            # Read the file JSON.
            filePath = os.path.join(globalDefinitionsDirectory, fileName)
            with open(filePath, encoding="utf-8") as file:
                definition = json.loads(file.read())

            # Set the overrides.
            for overrideName in PRINTER_OVERRIDES[fileName]:
                definition["overrides"][overrideName] = PRINTER_OVERRIDES[fileName][overrideName]

            # Save the file.
            with open(os.path.join(settingsDefinitionsDirectory, fileName), "w", encoding="utf-8") as file:
                file.write(json.dumps(definition, indent=4))

    # Copy and modify the materials.
    settingsMaterialsDirectory = os.path.join(targetSettings, "materials")
    globalMaterialsDirectory = os.path.join(latestCuraDirectory,"share","cura","resources", "materials")
    if not os.path.exists(settingsMaterialsDirectory):
        os.makedirs(settingsMaterialsDirectory)
    for materialFileName in MATERIAL_OVERRIDES:
        # Read the initial file.
        import xml.etree.ElementTree as ElementTree
        with open(os.path.join(globalMaterialsDirectory, materialFileName)) as file:
            materialXml = ElementTree.fromstring(file.read())

        # Apply the modifications.
        for settingName in MATERIAL_OVERRIDES[materialFileName].keys():
            for child in materialXml:
                if "settings" in child.tag:
                    for childSetting in child:
                        if "key" in childSetting.attrib.keys() and childSetting.attrib["key"] == settingName:
                           childSetting.text = str(MATERIAL_OVERRIDES[materialFileName][settingName])

        # Save the changes.
        with open(os.path.join(settingsMaterialsDirectory, materialFileName), "bw") as file:
            file.write(ElementTree.tostring(materialXml, encoding='utf8', method='xml'))

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