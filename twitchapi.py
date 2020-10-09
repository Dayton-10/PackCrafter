import requests
import json

# Uses the Twitch App API: https://twitchappapi.docs.apiary.io/

# 'Constant' values
MC_GAME_ID = 432
HEADERS = {'User-Agent': 'ModpackBot/1.0'} # Extra header defining bot User-Agent
URL_GET_ADDON_INFO             = 'https://addons-ecs.forgesvc.net/api/v2/addon/{}'
URL_TWITCH_ADDON_SEARCH        = 'https://addons-ecs.forgesvc.net/api/v2/addon/search?gameId={}&searchFilter={}'
URL_GET_ADDON_FILES            = 'https://addons-ecs.forgesvc.net/api/v2/addon/{}/files'
URL_GET_MINECRAFT_VERSION_LIST = 'https://addons-ecs.forgesvc.net/api/v2/minecraft/version'
URL_GET_MODLOADER_LIST         = 'https://addons-ecs.forgesvc.net/api/v2/minecraft/modloader'

# Sends a get request to the provided URL, and returns the result as a JSON
def twitchAPI(url, headers):
	response = requests.get(url, headers=headers)
	# Check for successful response (HTTP 200: OK)
	if response.status_code != 200 :
		print("Error: " + str(response.status_code))
		exit()
	return response.json()

# Returns the JSON response to the "Get Addon Info" Twitch API call
#   Behavior defined at: https://twitchappapi.docs.apiary.io/#/reference/0/get-addon-info/get-addon-info/200?mc=reference%2F0%2Fget-addon-info%2Fget-addon-info%2F200
def getAddonInfo(addonID):
	return twitchAPI(URL_GET_ADDON_INFO.format(addonID), HEADERS)

# Returns the JSON response to the "Twitch Addon Search" Twitch API call
#   Behavior defined at: https://twitchappapi.docs.apiary.io/#/reference/0/twitch-addon-search/twitch-addon-search/200?mc=reference%2F0%2Ftwitch-addon-search%2Ftwitch-addon-search%2F200
def twitchAddonSearch(searchFilter):
	return twitchAPI(URL_TWITCH_ADDON_SEARCH.format(MC_GAME_ID, searchFilter), HEADERS)

# Returns the JSON response to the "Get Addon Files" Twitch API call
#   Behavior defined at: https://twitchappapi.docs.apiary.io/#/reference/0/get-addon-files/get-addon-files/200?mc=reference%2F0%2Fget-addon-files%2Fget-addon-files%2F200
def getAddonFiles(addonID):
	return twitchAPI(URL_GET_ADDON_FILES.format(addonID), HEADERS)

# Returns the JSON response to the "Get Minecraft Version List" Twitch API call
#   Behavior defined at: https://twitchappapi.docs.apiary.io/#/reference/0/get-minecraft-version-list/get-minecraft-version-list/200?mc=reference%2F0%2Fget-minecraft-version-list%2Fget-minecraft-version-list%2F200
def getMinecraftVersionList():
	return twitchAPI(URL_GET_MINECRAFT_VERSION_LIST, HEADERS)

# Returns the JSON response to the "Get Modloader List" Twitch API call
#   Behavior defined at: https://twitchappapi.docs.apiary.io/#/reference/0/get-modloader-list/get-modloader-list/200?mc=reference%2F0%2Fget-modloader-list%2Fget-modloader-list%2F200
def getModloaderList():
	return twitchAPI(URL_GET_MODLOADER_LIST, HEADERS)
