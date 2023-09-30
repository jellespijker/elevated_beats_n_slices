import platform
from UM.i18n import i18nCatalog


catalog = i18nCatalog("cura")

from . import ElevatedBeatsNSlicesPlugin


def getMetaData():
    return {}

def register(app):
    return { "extension":  ElevatedBeatsNSlicesPlugin.ElevatedBeatsNSlicesPlugin() }

