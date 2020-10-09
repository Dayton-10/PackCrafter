from enum import IntEnum
import os

import twitchapi

def getDownloadPath():
    """Returns the default downloads path for linux or windows"""
    if os.name == 'nt':
        import winreg
        sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
        downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            location = winreg.QueryValueEx(key, downloads_guid)[0]
        return location
    else:
        return os.path.join(os.path.expanduser('~'), 'downloads')

# Class containing several Mod objects to simplify dependency resolution
#   Creating an entirely new Mod object for each File's dependency is too expensive, tracking already-found mods is much nicer
class ModList:
	# Instance variables:
	#   mods - a dict of addonIDs and their associated Mod objects
	def __init__(self):
		self.mods = {}

	def addMod(self, mod):
		if mod.addonID in self.mods:
			print("{} is already in the modlist!".format(mod.modName))
			return
		print("Adding new mod:")
		print(mod)
		self.mods[mod.addonID] = mod

# Class containing all the relevant information about a Mod
#   Inherits instance variable "modList" from the parent ModList
class Mod():
	# Instance variables:
	#   modList - a reference to the ModList this Mod object is referenced in
	#   addonID - the CurseForge "Addon ID" for this mod
	#   modName - the name of the mod
	#   modURL  - a string containing the URL for this mod on CurseForge (useful for checking license)
	#   authors - a list of strings containing all the authors for this mod
	#   files   - a list of File objects of all the files available for this mod on CurseForge

	# Constructor
	# Creates a new Mod object based on a chosen search result from the twitchAddonSearch() function
	#   Will populate instance variable "files" with File objects through a getAddonFiles() call
	def __init__(self, modList, addonSearchResult = None, addonID = None):
		self.modList = modList

		# If only given addonID, get addon information using getAddonInfo() call
		if addonSearchResult == None and addonID != None:
			addonSearchResult = twitchapi.getAddonInfo(addonID)

		# Initialize instance variables
		self.addonID = addonSearchResult['id']
		self.modName = addonSearchResult['name']
		self.modURL  = addonSearchResult['websiteUrl']
		self.authors = [entry['name'] for entry in addonSearchResult['authors']]

		# Initialize list of File objects
		self.files = []
		fileInfo = twitchapi.getAddonFiles(self.addonID)
		for fileListItem in fileInfo:
			self.files.append(File(self, fileListItem))

		self.selectedFile = None

	def __str__(self):
		result = ''
		result = result + 'Mod ID {}:\n'.format(self.addonID)
		result = result + '  Name: {}\n'.format(self.modName)
		result = result + '  {} files\n'.format(len(self.files))
		return result

# Enumeration for dependency types
#   Values obtained empirically from the Twitch API
class DependencyType(IntEnum):
	REQUIRED = 3 # Defined as 3 based-off of CurseForge API, where "type" field of dependency is 3 if required
	OPTIONAL = 2 # Defined as 2 based-off of CurseForge API, where "type" field of dependency is 2 if optional

# Enumeration for File release types
#   Values obtained empirically from the Twitch API
class ReleaseType(IntEnum):
	RELEASE = 1
	BETA    = 2
	ALPHA   = 3

# Class containing all the relevant information about a File for a mod
#   Inherits instance variable "mod" from the parent Mod
class File():
	# Instance variables:
	#   mod          - a reference to the Mod object this File object is a referenced in
	#   mcVersion    - a string containing the version of Minecraft this file is for
	#   fileID       - the CurseForge "File ID" for this file
	#   fileName     - the name of the file on CurseForge (includes extension)
	#   fileURL      - a string containing the download URL for this file on CurseForge
	#   releaseType  - a ReleaseType enum value stating whether this file is Alpha, Beta, or Release
	#   dependencies - a list of tuples of Mod objects this file (optionally) depends on to function and a Dependency enum value stating whether it's a required/optional dependency

	# Constructor
	# Creates a new File object based on a chosen file from a getAddonFiles() call
	def __init__(self, mod, fileListItem):
		self.mod       = mod
		for gameVersion in fileListItem['gameVersion']:
			if gameVersion != 'Forge':
				self.mcVersion = gameVersion
		self.fileID      = fileListItem['id']
		self.fileName    = fileListItem['fileName']
		self.fileURL     = fileListItem['downloadUrl']
		self.releaseType = ReleaseType(fileListItem['releaseType'])

		# Parse dependencies and create a (Mod, Dependency(Enum)) tuple for each and add it to the dependencies list
		self.dependencies = []
		for dependency in fileListItem['dependencies']:
			if dependency['type'] == DependencyType.REQUIRED: # Only look for required dependencies
				if dependency['addonId'] in self.mod.modList.mods:
					#print("Found existing mod dependency for {}: {}".format(self.mod.modName, self.mod.modList.mods[dependency['addonId']].modName))
					self.dependencies.append((self.mod.modList.mods[dependency['addonId']], DependencyType(dependency['type'])))
				else:
					newMod = Mod(mod.modList, addonID=dependency['addonId'])
					print("Found new mod dependency {}: adding to ModList".format(newMod.modName))
					self.mod.modList.addMod(newMod)
					self.dependencies.append((self.mod.modList.mods[dependency['addonId']], DependencyType(dependency['type'])))

	def __str__(self):
		result = ''
		result = result + 'File ID: {}\n'.format(self.fileID)
		result = result + '  Name: {}\n'.format(self.fileName)
		result = result + '  {} dependencies:\n'.format(len(self.dependencies))
		for dependency in self.dependencies:
			result = result + '{}{}\n'.format(dependency[0], dependency[1].name)
		return result

	# Downloads this file from the fileURL
	def download(self):
		req = requests.get(self.fileURL, HEADERS, stream=True)
		with open(getDownloadPath()+'\\modpack\\'+self.fileName, 'wb') as fd:
			for chunk in req.iter_content(chunk_size=128):
				fd.write(chunk)

