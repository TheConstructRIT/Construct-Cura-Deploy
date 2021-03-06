"""
Zachary Cook

Patches files in Cura. May need to be run as admin.
"""

import os
import shutil
from Configuration import KNOWN_CURA_LOCATIONS


def applyPatch(targetDirectory: str, patchFile: str) -> None:
    """Applies a patch file to a file in the given directory.

    :param targetDirectory: Directory containing the file.
    :param patchFile: Patch file to apply.
    """

    targetFile = os.path.join(targetDirectory, os.path.basename(patchFile).lower().replace(".patch", ""))

    # Get the patch sections.
    patchSections = []
    currentSection = ""
    with open(patchFile) as file:
        for line in file.readlines():
            line = line.replace("\r", "").replace("\n", "")
            if line.startswith("====="):
                patchSections.append(currentSection)
                currentSection = ""
            else:
                if currentSection == "":
                    currentSection = line
                else:
                    currentSection += "\n" + line
    if currentSection != "":
        patchSections.append(currentSection)

    # Throw an error if there aren't an even amount of sections.
    if len(patchSections) % 2 != 0:
        raise Exception("There an odd amount of sections in the patch file " + patchFile)

    # Ensure a recursive patch doesn't exist.
    for i in range(0, len(patchSections), 2):
        if patchSections[i + 1].replace(patchSections[i], patchSections[i + 1]) != patchSections[i + 1]:
            raise Exception("At least 1 patch is recursive (able to be patched repeatedly).")

    # Apply the patches to the file.
    with open(targetFile) as file:
        patchedContents = file.read()
        for i in range(0, len(patchSections), 2):
            patchedContents = patchedContents.replace(patchSections[i], patchSections[i + 1])
    with open(targetFile, "w") as file:
        file.write(patchedContents)


def patchDirectory(targetFileOrDirectory: str, sourceFileOrDirectory: str) -> None:
    """Patches a file or directory.

    :param targetFileOrDirectory: File or directory to patch.
    :param sourceFileOrDirectory: File or directory of the patches.
    """

    if os.path.isdir(sourceFileOrDirectory):
        # Iterate over the patch directories.
        for directory in os.listdir(sourceFileOrDirectory):
            patchDirectory(os.path.join(targetFileOrDirectory, directory), os.path.join(sourceFileOrDirectory, directory))
    elif os.path.isfile(sourceFileOrDirectory):
        if sourceFileOrDirectory.lower().endswith(".patch"):
            # Apply the patch files.
            applyPatch(os.path.dirname(targetFileOrDirectory), sourceFileOrDirectory)
        else:
            # Copy the file.
            if os.path.exists(targetFileOrDirectory):
                os.remove(targetFileOrDirectory)
            shutil.copy(sourceFileOrDirectory, targetFileOrDirectory)


def patchCuraInstall(curaDirectory: str) -> None:
    """Patches an install of Cura.

    :param curaDirectory: Directory of Cura to patch.
    """

    # Apply the patch files.
    patchesDirectory = os.path.realpath(os.path.join(__file__, "..", "patches"))
    patchDirectory(curaDirectory, patchesDirectory)


def patchCuraInstalls() -> None:
    """Patches all installs of Cura installed to the known locations.
    """

    for knownLocation in KNOWN_CURA_LOCATIONS:
        if os.path.isdir(knownLocation):
            for directory in os.listdir(knownLocation):
                if "ultimaker cura" in directory.lower():
                    patchCuraInstall(os.path.join(knownLocation, directory))


if __name__ == '__main__':
    patchCuraInstalls()
