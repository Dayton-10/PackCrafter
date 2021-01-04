import tkinter
from tkinter import ttk
from packaging import version
from enum import IntEnum
from collections import namedtuple
import json
import webbrowser
import os
from zipfile import ZipFile
import shutil

import twitchapi
import modlist

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

# Scrollable Frame Class, courtesy of https://gist.github.com/mp035/9f2027c3ef9172264532fcd6262f3b01
#   Modified to accept a width parameter (set to 25 by default)
class ScrollFrame(tkinter.Frame):
    def __init__(self, parent, width=25):
        super().__init__(parent) # create a frame (self)

        self.canvas = tkinter.Canvas(self, borderwidth=0, background="#ffffff", width=width)          #place canvas on self
        self.viewPort = tkinter.Frame(self.canvas, background="#ffffff", width=width)                 #place a frame on the canvas, this frame will hold the child widgets 
        self.vsb = tkinter.Scrollbar(self, orient="vertical", command=self.canvas.yview) #place a scrollbar on self 
        self.canvas.configure(yscrollcommand=self.vsb.set)                          #attach scrollbar action to scroll of canvas

        self.vsb.pack(side="right", fill="y")                                       #pack scrollbar to right of self
        self.canvas.pack(side="left", fill="both", expand=True)                     #pack canvas to left of self and expand to fil
        self.canvas_window = self.canvas.create_window((4,4), window=self.viewPort, anchor="nw",            #add view port frame to canvas
                                  tags="self.viewPort")

        self.viewPort.bind("<Configure>", self.onFrameConfigure)                       #bind an event whenever the size of the viewPort frame changes.
        self.canvas.bind("<Configure>", self.onCanvasConfigure)                       #bind an event whenever the size of the viewPort frame changes.

        self.onFrameConfigure(None)                                                 #perform an initial stretch on render, otherwise the scroll region has a tiny border until the first resize

    def onFrameConfigure(self, event):                                              
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))                 #whenever the size of the frame changes, alter the scroll region respectively.

    def onCanvasConfigure(self, event):
        '''Reset the canvas window to encompass inner frame when required'''
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width = canvas_width)            #whenever the size of the canvas changes alter the window region respectively.



class Application():
	# Instance variables:

	# mainWindow               - a reference to the application's main window
	#   frameModpackName       - a frame to hold the modpack name widgets
	#     labelModpackName     - a label for modpack name entry widget
	#     entryModpackName     - an entry widget where the user can input a name for their modpack
	#   frameModpackVersion    - a frame to hold the modpack version widgets
	#     labelModpackVersion  - a label for modpack version entry widget
	#     entryModpackVersion  - an entry widget where the user can input a version for their modpack
	#   frameModpackAuthor     - a frame to hold modpack author widgets
	#     labelModpackAuthor   - a label for modpack author entry widget
	#     entryModpackAuthor   - an entry widget for modpack author
	#   frameMCVersion         - a frame to hold Minecraft version widgets
	#     labelMCVersion       - a label for Minecraft version combobox widget
	#     comboboxMCVersion    - aombobox widget for selecting pack Minecraft version
	#   frameForgeVersion      - a frame to hold Forge version widgets
	#     labelForgeVersion    - a label for Forge version combobox widget
	#     comboboxForgeVersion - a combobox widget for selecting pack Forge version
	#   scrollFrameModList     - a ScrollFrame displaying currently added mods

	# minecraftVersion - a string containing the selected Minecraft version; updated whenever a new Minecraft version is chosen. None by default
	# forgeVersion     - a string containing the selected Forge version; updated whenever a new Minecraft and/or Forge version is chosen. None by default
	# modList          - a ModList object containing all the Mods a user adds to the modpack
	# modListWidgets   - a dict of {modID: tuples}, where the tuples are of Tkinter widgets for displaying each Mod: (labelModName, comboboxFileName, comboboxFileDict, labelModAuthors, labelModLicense, buttonModRemove)
	#                    comboboxFileDict is a dict where File names with added-on A/B/R information are the keys for a specific File

	def __init__(self):
		self.modList = modlist.ModList()
		self.minecraftVersion = None
		self.forgeVersion = None

		# Setup named tuple and list of aforementioned tuples for organizing ModList widgets
		self.ModListWidget = namedtuple('ModListWidget', 'labelModName comboboxFileName comboboxFileDict labelModAuthors labelModLicense buttonModRemove')
		self.modListWidgets = {}

		# Setup main window
		self.mainWindow = tkinter.Tk()
		self.mainWindow.geometry("700x700")
		#self.mainWindow.resizable(False, False) # Make the main window not resizable
		self.mainWindow.resizable(True, True) # Make the main window resizable
		self.mainWindow.title("PackCrafter Alpha")

		# Grid resizing configuration
		for i in range(3):
			self.mainWindow.columnconfigure(i, weight=1, minsize=150)
		for i in range(2):
			self.mainWindow.rowconfigure(i, weight=1, minsize=50)

		# Setup modpack name entry
		self.frameModpackName = tkinter.Frame(master=self.mainWindow, borderwidth=2)
		self.frameModpackName.grid(row=0, column=0, padx=5, pady=5)
		self.labelModpackName = tkinter.Label(self.frameModpackName, text='Modpack Name')
		self.labelModpackName.pack()
		self.entryModpackName = tkinter.Entry(self.frameModpackName)
		self.entryModpackName.pack()

		# Setup modpack version entry
		self.frameModpackVersion = tkinter.Frame(master=self.mainWindow)
		self.frameModpackVersion.grid(row=0, column=1, padx=5, pady=5)
		self.labelModpackVersion = tkinter.Label(self.frameModpackVersion, text='Modpack Version')
		self.labelModpackVersion.pack()
		self.entryModpackVersion = tkinter.Entry(self.frameModpackVersion)
		self.entryModpackVersion.pack()

		# Setup modpack author entry
		self.frameModpackAuthor = tkinter.Frame(master=self.mainWindow)
		self.frameModpackAuthor.grid(row=0, column=2, padx=5, pady=5)
		self.labelModpackAuthor = tkinter.Label(self.frameModpackAuthor, text='Modpack Author')
		self.labelModpackAuthor.pack()
		self.entryModpackAuthor = tkinter.Entry(self.frameModpackAuthor)
		self.entryModpackAuthor.pack()

		# Setup minecraft version selection
		self.frameMCVersion = tkinter.Frame(master=self.mainWindow)
		self.frameMCVersion.grid(row=1, column=0, padx=5, pady=5)
		self.labelMCVersion = tkinter.Label(self.frameMCVersion, text='Minecraft Version')
		self.labelMCVersion.pack()
		self.comboboxMCVersion = ttk.Combobox(self.frameMCVersion, values = [entry['versionString'] for entry in twitchapi.getMinecraftVersionList()], state="readonly", width=10)
		self.comboboxMCVersion.pack()
		self.comboboxMCVersion.bind('<<ComboboxSelected>>', self.selectMinecraftVersion)

		# Setup forge version selection
		self.frameForgeVersion = tkinter.Frame(master=self.mainWindow)
		self.frameForgeVersion.grid(row=1, column=1, columnspan=2, padx=5, pady=5)
		self.labelForgeVersion = tkinter.Label(self.frameForgeVersion, text='Forge Version')
		self.labelForgeVersion.pack()
		self.comboboxForgeVersion = ttk.Combobox(self.frameForgeVersion, width=45, state="disabled", values=["Choose a Minecraft version"])
		self.comboboxForgeVersion.current(0)
		self.comboboxForgeVersion.pack()
		self.comboboxForgeVersion.bind('<<ComboboxSelected>>', self.selectForgeVersion)
		self.forgeVersionDict = {} # A dict for storing {"Forge name string w/ recommended/latest info": "normal Forge name string"}

		# Setup mod list section
		self.scrollFrameModList = ScrollFrame(self.mainWindow, width=1920)
		self.scrollFrameModList.grid(row=2, column=0, rowspan=5, columnspan=3)

		# Setup add mod button
		self.frameAddMod = tkinter.Frame(master=self.mainWindow)
		self.frameAddMod.grid(row=7, column=2, padx=5, pady=15)
		self.buttonAddMod = tkinter.Button(master=self.frameAddMod, text='Add Mod', command=lambda: self.AddModDialog(self))
		self.buttonAddMod.pack()

		# Create a button to create the modpack
		tkinter.Button(master=self.mainWindow, text='Create Modpack', command=lambda: self.createModpack()).grid(row=11, column=2)

		self.mainWindow.mainloop()

	# Nested class for the Add Mod dialog
	class AddModDialog():
		def __init__(self, application):
			#print("User wants to add a mod")
			self.application = application

			# Setup dialog window
			self.window = tkinter.Toplevel(self.application.mainWindow)
			self.window.geometry("500x300")
			self.window.resizable(False, False)

			# Setup searchbox
			self.entrySearchbox = tkinter.Entry(master=self.window, text='Mod Name')
			self.entrySearchbox.grid(row=0, column=0, columnspan=2)
			self.buttonSearchbox = tkinter.Button(master=self.window, text='Search', command=lambda: self.updateModList())
			self.buttonSearchbox.grid(row=0, column=2)

			# Setup mod list
			self.listboxModList = tkinter.Listbox(master=self.window, width=50, selectmode=tkinter.SINGLE)
			self.listboxModList.grid(row=1, column=0, rowspan=5, columnspan=2)
			self.listboxModList.bind("<<ListboxSelect>>", self.updateButtonAddMod)

			# Setup add button
			self.buttonAddMod = tkinter.Button(master=self.window, text='Add Mod', state=tkinter.DISABLED, command=lambda: self.addMod())
			self.buttonAddMod.grid(row=6, column=1)

			self.window.mainloop()

		def updateButtonAddMod(self, event=None):
			if self.listboxModList.curselection() == (): # Will return empty tuple if nothing is currently selected
				self.buttonAddMod['state'] = tkinter.DISABLED
			else:
				self.buttonAddMod['state'] = tkinter.NORMAL

		def updateModList(self):
			self.listboxModList.delete(0, self.listboxModList.size())
			self.mods = [entry for entry in twitchapi.twitchAddonSearch(self.entrySearchbox.get()) if entry['categorySection']['name'] == 'Mods']
			for mod in self.mods:
				self.listboxModList.insert(tkinter.END, mod['name'])

		def addMod(self):
			print("User wants to add mod {}".format(self.mods[self.listboxModList.curselection()[0]]['name']))
			self.application.modList.addMod(modlist.Mod(self.application.modList, addonSearchResult=self.mods[self.listboxModList.curselection()[0]]))
			self.application.updateModList()

	# Callback function for when a version of Minecraft is selected using the combobox
	#   Will check if a new version was selected, and update other widgets accordingly
	def selectMinecraftVersion(self, event=None):
		newMinecraftVersion = self.comboboxMCVersion.get()
		if newMinecraftVersion == self.minecraftVersion: # If Minecraft version didn't change
			return                                       #   Do nothing
		self.minecraftVersion = newMinecraftVersion      # Otherwise, update Forge versions and Mod list
		self.updateForgeVersions()
		self.updateModList()

	# Callback function for when a version of Forge is selected using the combobox
	def selectForgeVersion(self, event=None):
		self.forgeVersion = self.forgeVersionDict[self.comboboxForgeVersion.get()]
		print(self.forgeVersion)

	# Update the forge version combobox
	def updateForgeVersions(self):
		sortedVersions = sorted([entry for entry in twitchapi.getModloaderList() if entry['gameVersion'] == self.minecraftVersion], key=lambda x : version.parse(x['name']), reverse=True)
		#print(sortedVersions)
		#forgeList = []
		self.forgeVersionDict = {}
		for versionEntry in sortedVersions:
			versionString = versionEntry['name']
			if versionEntry['recommended']:
				#versionString = versionString + '  Recommended'
				self.forgeVersionDict[versionString + ' (Recommended)'] = versionString
			if versionEntry['latest']:
				#versionString = versionString + '  Latest'
				self.forgeVersionDict[versionString + ' (Latest)'] = versionString
			else:
				self.forgeVersionDict[versionString] = versionString
			#forgeList.append(versionString)
		self.comboboxForgeVersion['state'] = "readonly"
		#self.comboboxForgeVersion['values'] = forgeList
		self.comboboxForgeVersion['values'] = [key for key, value in self.forgeVersionDict.items()]
		try:
			self.comboboxForgeVersion.current(0)
			self.selectForgeVersion()
		except:
			self.comboboxForgeVersion['state'] = "disabled"
			self.comboboxForgeVersion['values'] = ["No available Forge for this version of Minecraft"]
			self.comboboxForgeVersion.current(0)
			self.forgeVersion = None

	# Create the modpack's manifest
	#   Returns the generated manifest structure to be written as a JSON separately
	def createManifest(self):
		manifest = {
			"minecraft": {
				"version": self.minecraftVersion,
				"modLoaders": [
						{
							"id": self.forgeVersion,
							"primary": True
						}
					]
				},
			"manifestType": "minecraftModpack",
			"manifestVersion": 1,
			"name": self.entryModpackName.get(),
			"version": self.entryModpackVersion.get(),
			"author": self.entryModpackAuthor.get(),
			"files": [],
			"overrides": "overrides"
			}

		# Add selected Mod Files to manifest (means each Mod doesn't need to be downloaded)
		for modID, mod in self.modList.mods.items():
			if mod.selectedFile != None:
				modManifest = {}
				modManifest['projectID'] = mod.addonID
				modManifest['fileID'] = mod.selectedFile.fileID
				modManifest['required'] = True
				manifest['files'].append(modManifest)

		print(json.dumps(manifest))
		return manifest
		
	# Creates a modpack modlist with credits
	#   Returns the generated HTML string to be written as an HTML file separately
	def createModpackCredits(self):
		html = "<!DOCTYPE html><html><body>\n"

		# Write modpack information to HTML string
		html = html + "<h1>Modpack Information</h1><p>Name: {}</p><p>Version: {}</p><p>Author: {}</p><p>Minecraft Version: {}</p><p>Forge Version: {}</p>".format(self.entryModpackName.get(), self.entryModpackVersion.get(), self.entryModpackAuthor.get(), self.minecraftVersion, self.forgeVersion)

		# Write mod information to HTML string
		html = html + "<h1>Mod Credits</h1>"
		for modID, mod in self.modList.mods.items(): # For every mod with a selected file
			if mod.selectedFile != None:
				html = html + "<h2>{}</h2>".format(mod.modName)
				html = html + "<p>Version: {}</p><p>Author(s): {}</p><p>Website: {}</p>".format(mod.selectedFile.fileName, mod.authors, mod.modURL)

		html = html + "</body></html>"
		return html

	# Creates a modpack folder in the user's "Downloads" directory, then adds a generated manifest.json and zips the folder for easy import into MultiMC
	# TODO: Check to make sure MC/Forge versions are valid, and that the modpack has a name/version/author
	# TODO: Checkbox to allow user to specify whether or not to zip the modpack when done
	def createModpack(self):
		modpackFolder = getDownloadPath() + '\\{}'.format(self.entryModpackName.get())
		try:
			os.mkdir(modpackFolder)
			os.mkdir(modpackFolder + '\\overrides')
			os.mkdir(modpackFolder + '\\overrides\\mods')
			os.mkdir(modpackFolder + '\\overrides\\config')
			os.mkdir(modpackFolder + '\\overrides\\resources')
			os.mkdir(modpackFolder + '\\overrides\\scripts')
		except FileExistsError:
			pass
		with open(modpackFolder + '\\manifest.json', 'w') as manifestFile:
			json.dump(self.createManifest(), manifestFile)
		with open(modpackFolder + '\\credits.html', 'w') as creditsFile:
			creditsFile.write(self.createModpackCredits())

		# Zip the modpack for easy import into MultiMC
		#shutil.make_archive(modpackFolder, 'zip', modpackFolder)


	# Update all the available files in the combobox for each mod in the modpack
	# #TODO: Don't replace selected files when adding a new mod
	def updateModList(self):
		#print("Updated mod list is:")
		#self.modListWidgets = {}
		i = 0
		for modID, mod in self.modList.mods.items():

			mod.selectedFile = None

			# If mod already has a set of widgets:
			if modID in self.modListWidgets:
				print("Mod {} already has widgets. Updating widgets".format(mod.modName))
			# If mod doesn't have a set of widgets yet:
			else:
				print("Creating new widgets for Mod {}".format(mod.modName))
				# Create Mod name label
				labelName = tkinter.Label(self.scrollFrameModList.viewPort, text=mod.modName)
				labelName.grid(row=i, column=0)
				# Create Mod Files list combobox
				combobox = ttk.Combobox(self.scrollFrameModList.viewPort, state="readonly", width=45)
				combobox.grid(row=i, column=1)
				# Create Mod authors label
				labelAuthor = tkinter.Label(self.scrollFrameModList.viewPort, text=mod.authors)
				labelAuthor.grid(row=i, column=2)
				# Create Mod Curseforge page hyperlink label
				labelLicense = tkinter.Label(self.scrollFrameModList.viewPort, text='Curseforge Page', fg="blue") # Setup label like a hyperlink
				labelLicense.grid(row=i, column=3)
				labelLicense.bind("<Button-1>", lambda e, url=mod.modURL: webbrowser.open_new(url)) # Open mod webpage in user's browser if clicked-on
				# Create Mod removal button
				button = tkinter.Button(self.scrollFrameModList.viewPort, text='X', command=lambda m=modID: self.removeMod(m))
				button.grid(row=i, column=4)
				# Add above widgets to a ModListWidgets named tuple for this mod
				widgets = self.ModListWidget(labelName, combobox, {}, labelAuthor, labelLicense, button)
				self.modListWidgets[modID] = widgets

			# Put Mod Files in combobox
			modFiles = sorted([file for file in mod.files if (self.minecraftVersion in file.mcVersions)], key=lambda x: version.parse(x.fileName), reverse=True)

			# If no Minecraft version is selected:
			if self.minecraftVersion == None:
				self.modListWidgets[modID].comboboxFileName['values'] = ['Select a version of Minecraft']
				self.modListWidgets[modID].comboboxFileName['state'] = 'disabled'
				self.modListWidgets[modID].comboboxFileName.current(0)
			# If no Files exist for this version of Minecraft:
			elif modFiles == []:
				self.modListWidgets[modID].comboboxFileName['values'] = ['No files for this version of Minecraft']
				self.modListWidgets[modID].comboboxFileName['state'] = 'disabled'
				self.modListWidgets[modID].comboboxFileName.current(0)
			# Otherwise, list relevant Files
			else:
				self.modListWidgets[modID].comboboxFileDict.clear(); # Reset file dictionary
				for file in modFiles:
					# Record File release type
					if file.releaseType == modlist.ReleaseType.ALPHA:
						self.modListWidgets[modID].comboboxFileDict[file.fileName + " (Alpha)"] = file
					elif file.releaseType == modlist.ReleaseType.BETA:
						self.modListWidgets[modID].comboboxFileDict[file.fileName + " (Beta)"] = file
					elif file.releaseType == modlist.ReleaseType.RELEASE:
						self.modListWidgets[modID].comboboxFileDict[file.fileName + " (Release)"] = file
					else:
						self.modListWidgets[modID].comboboxFileDict[file.fileName + " (Unknown Type)"] = file

				# Setup combobox with list of valid files
				self.modListWidgets[modID].comboboxFileName['values'] = ['Choose a mod file']
				self.modListWidgets[modID].comboboxFileName.current(0)
				self.modListWidgets[modID].comboboxFileName['values'] = [key for key, value in self.modListWidgets[modID].comboboxFileDict.items()]
				self.modListWidgets[modID].comboboxFileName['state'] = 'readonly'
				self.modListWidgets[modID].comboboxFileName.bind('<<ComboboxSelected>>', lambda e, m=mod: self.setModSelectedFile(m, self.modListWidgets[m.addonID].comboboxFileDict[self.modListWidgets[m.addonID].comboboxFileName.get()]))
			
			i = i + 1

	# Set the Mod's selectedFile variable to File
	def setModSelectedFile(self, mod, file):
		print("Set File for {} to {}".format(mod.modName, file.fileName))
		mod.selectedFile = file

	# Removes the Mod with the given modID from the ModList and remove its associated widgets from modListWidgets
	def removeMod(self, modID):
		removedMod = self.modList.mods.pop(modID) # Remove Mod from ModList
		print(removedMod)
		print(self.modList.mods)
		removedWidgets = self.modListWidgets.pop(modID) # Remove ModListWidget from modListWidgets
		for widget in removedWidgets: # Remove widgets from the window, then destroy them
			if widget != removedWidgets.comboboxFileDict:
				tkinter.Grid.grid_remove(widget)
				widget.destroy()
			else:
				widget.clear()
		self.updateModList()

# Run application
packCrafter = Application()