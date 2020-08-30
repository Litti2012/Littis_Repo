# -*- coding: utf-8 -*-

import sys
import re
import xbmc
import xbmcgui
import xbmcplugin
import json
import xbmcvfs
import time
from datetime import datetime, timedelta
from collections import OrderedDict
PY2 = sys.version_info[0] == 2
if PY2:
	from urllib import urlencode, quote_plus  # Python 2.X
else: 
	from urllib.parse import urlencode, quote_plus  # Python 3.X

from .common import *


if not xbmcvfs.exists(dataPath):
	xbmcvfs.mkdirs(dataPath)

def mainMenu():
	addDir(translation(30601), icon, {'mode': 'listShowsFavs'})
	addDir(translation(30602), icon, {'mode': 'listSeries', 'url': BASE_API+'/content/shows?include=images&sort=name', 'extras': 'overview_all'})
	addDir(translation(30603), icon, {'mode': 'listAlphabet', 'extras': 'letter_A-Z'})
	addDir(translation(30604), icon, {'mode': 'listThemes', 'url': BASE_API+'/content/genres?include=images&page[size]=50'})
	addDir(translation(30605), icon, {'mode': 'listSeries', 'url': BASE_API+'/content/shows?include=images&sort=publishEnd&filter[hasExpiringEpisodes]=true', 'extras': 'last_chance'})
	addDir(translation(30606), icon, {'mode': 'listSeries', 'url': BASE_API+'/content/shows?include=images&sort=-newestEpisodePublishStart&filter[hasNewEpisodes]=true', 'extras': 'recently_added'})
	addDir(translation(30607), icon, {'mode': 'listSeries', 'url': BASE_API+'/content/shows?include=images&sort=views.lastWeek', 'extras': 'most_popular'})
	if enableADJUSTMENT:
		addDir(translation(30608), artpic+'settings.png', {'mode': 'aSettings'})
		if enableINPUTSTREAM and ADDON_operate('inputstream.adaptive'):
			addDir(translation(30609), artpic+'settings.png', {'mode': 'iSettings'})
		else:
			addon.setSetting('useInputstream', 'false')
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listThemes(url):
	debug_MS("(navigator.listThemes) ------------------------------------------------ START = listThemes -----------------------------------------------")
	content = getUrl(url)
	debug_MS("++++++++++++++++++++++++")
	debug_MS("(navigator.listThemes) XXXXX CONTENT : {0} XXXXX".format(str(content)))
	debug_MS("++++++++++++++++++++++++")
	DATA = json.loads(content, object_pairs_hook=OrderedDict)
	for elem in DATA['data']:
		genreID = str(elem['id'])
		name = cleaning(elem['attributes']['name'])
		image = icon
		for attr in DATA['included']:
			if 'attributes' in attr and 'src' in attr['attributes'] and attr['attributes']['src'] != "" and attr['attributes']['src'] is not None:
				if 'genre-'+genreID+'-' in attr['attributes']['src']:
					image = attr['attributes']['src']
		newURL = '{0}/content/shows?include=images&sort=name&filter[genre.id]={1}'.format(BASE_API, genreID)
		addDir(name, image, {'mode': 'listSeries', 'url': newURL, 'extras': 'overview_genres'})
		debug_MS("(navigator.listThemes) ### NAME : {0} || GENRE-ID : {1} ###".format(str(name), genreID))
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listAlphabet():
	debug_MS("(navigator.listAlphabet) ------------------------------------------------ START = listAlphabet -----------------------------------------------")
	for letter in '#ABCDEFGHIJKLMNOPQRSTUVWXYZ':
		newURL = '{0}/content/shows?include=images&sort=name&filter[name.startsWith]={1}'.format(BASE_API, letter.replace('#', '1'))
		addDir(letter, alppic+letter+'.png', {'mode': 'listSeries', 'url': newURL})
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listSeries(url, PAGE, POS, ADDITION):
	debug_MS("(navigator.listSeries) ------------------------------------------------ START = listSeries -----------------------------------------------")
	debug_MS("(navigator.listSeries) ### URL : {0} ### PAGE : {1} ### POS : {2} ### ADDITION : {3} ###".format(url, str(PAGE), str(POS), str(ADDITION)))
	UNIKAT = set()
	count = int(POS)
	complete_URL = url+'&page[number]={0}&page[size]=50'.format(str(PAGE))
	content = getUrl(complete_URL)
	debug_MS("++++++++++++++++++++++++")
	debug_MS("(navigator.listSeries) XXXXX CONTENT : {0} XXXXX".format(str(content)))
	debug_MS("++++++++++++++++++++++++")
	DATA = json.loads(content, object_pairs_hook=OrderedDict)
	for elem in DATA['data']:
		debug_MS("(navigator.listSeries) ##### ELEMENT : {0} #####".format(str(elem)))
		seriesID = ""
		if 'id' in elem and elem['id'] != "" and elem['id'] is not None:
			seriesID = str(elem['id'])
		if seriesID != "" and seriesID in UNIKAT:
			continue
		UNIKAT.add(seriesID)
		if 'attributes' in elem:
			elem = elem['attributes']
		if 'name' in elem and elem['name'] != "" and elem['name'] is not None:
			seriesNAME = cleaning(elem['name'])
		else: continue
		name = seriesNAME
		plot = ""
		if 'description' in elem and elem['description'] != "" and elem['description'] is not None:
			plot = cleaning(elem['description']).replace('\n\n\n', '\n\n')
		image = icon
		for attr in DATA['included']:
			if 'attributes' in attr and 'src' in attr['attributes'] and attr['attributes']['src'] != "" and attr['attributes']['src'] is not None:
				if 'show-'+seriesID+'-' in attr['attributes']['src']:
					image = attr['attributes']['src']
		debug_MS("(navigator.listSeries) noFilter ### NAME : {0} || SERIE-IDD : {1} || IMAGE : {2} ###".format(str(name), seriesID, image))
		if seriesID !="" and len(seriesID) < 9 and plot != "" and image != "":
			count += 1
			if 'views.lastWeek' in url:
				name = translation(30620).format(str(count), seriesNAME)
			elif 'filter[hasExpiringEpisodes]' in url:
				name = translation(30621).format(name)
			if not 'filter[hasExpiringEpisodes]' in url and 'hasNewEpisodes' in elem and elem['hasNewEpisodes'] != "" and elem['hasNewEpisodes'] is True:
				name = translation(30622).format(name)
			debug_MS("(navigator.listSeries) Filtered --- NAME : {0} || SERIE-IDD : {1} || IMAGE : {2} ---".format(str(name), seriesID, image))
			addType = 1
			if os.path.exists(channelFavsFile):
				with open(channelFavsFile, 'r') as output:
					lines = output.readlines()
					for line in lines:
						if line.startswith('###START'):
							part = line.split('###')
							if seriesID == part[3]: addType = 2
			if seriesNAME.lower() not in ['hgtv highlights']:
				addDir(name, image, {'mode': 'listEpisodes', 'url': seriesID, 'extras': ADDITION, 'origSERIE': seriesNAME}, plot, addType)
	currentRESULT = count
	debug_MS("(navigator.listSeries) NUMBERING ### currentRESULT : {0} ###".format(str(currentRESULT)))
	try:
		totalPG = DATA['meta']['totalPages']
		debug_MS("(navigator.listSeries) PAGES ### currentPG : {0} from totalPG : {1} ###".format(str(PAGE), str(totalPG)))
		if int(PAGE) < int(totalPG):
			addDir(translation(30623), artpic+'nextpage.png', {'mode': 'listSeries', 'url': url, 'page': int(PAGE)+1, 'position': int(currentRESULT), 'extras': ADDITION})
	except: pass
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listEpisodes(Xidd, origSERIE):
	debug_MS("(navigator.listEpisodes) ------------------------------------------------ START = listEpisodes -----------------------------------------------")
	debug_MS("(navigator.listEpisodes) ### URL : {0} ### origSERIE : {1} ###".format(str(Xidd), origSERIE))
	COMBI_EPISODE = []
	pos_SP = 0
	pageNUMBER = int(1)
	while pageNUMBER < int(5):
		newURL = '{0}/content/videos?include=images&sort=-seasonNumber,-episodeNumber&filter[show.id]={1}&filter[videoType]=EPISODE,STANDALONE&page[number]={2}&page[size]=100'.format(BASE_API, Xidd, str(pageNUMBER))
		content = getUrl(newURL)
		debug_MS("++++++++++++++++++++++++")
		debug_MS("(navigator.listEpisodes) XXXXX CONTENT : {0} XXXXX".format(str(content)))
		debug_MS("++++++++++++++++++++++++")
		DATA = json.loads(content, object_pairs_hook=OrderedDict)
		details = len(DATA['data'])
		if details > 0:
			pageNUMBER += int(1)
		else:
			pageNUMBER += int(4)
		debug_MS("(navigator.listEpisodes) ### newURL : {0} ### pageNUMBER : {1} ### origSERIE : {2} ###".format(newURL, str(pageNUMBER-1), str(origSERIE)))
		for vid in DATA['data']:
			genre, episID, plus_SUFFIX, videoTYPE, title2, number, Note_1, Note_2, Note_3 = ("" for _ in range(9))
			season, episode, duration = ('0' for _ in range(3))
			startTIMES, endTIMES, year, begins = (None for _ in range(4))
			genreLIST=[]
			if 'relationships' in vid and 'genres' in vid['relationships'] and 'data' in vid['relationships']['genres'] and vid['relationships']['genres']['data'] != "" and vid['relationships']['genres']['data'] is not None:
				for item in vid['relationships']['genres']['data']:
					try: gNames = convert(str(item['id']))
					except: gNames = ""
					genreLIST.append(gNames)
				genre =' / '.join(genreLIST)
			if 'id' in vid and vid['id'] != "" and vid['id'] is not None:
				episID = str(vid['id'])
			if 'attributes' in vid:
				vid = vid['attributes']
			if 'clearkeyEnabled' in vid and vid['clearkeyEnabled'] is True:
				debug_MS("(navigator.listEpisodes) ##### ELEMENT : {0} #####".format(str(vid)))
				if 'name' in vid and vid['name'] != "" and vid['name'] is not None:
					title = cleaning(vid['name'])
				else: continue
				if ('isExpiring' in vid and vid['isExpiring'] is True) or ('isNew' in vid and vid['isNew'] is True):
					plus_SUFFIX = translation(30624) if ('isNew' in vid and vid['isNew'] is True) else translation(30625)
				if 'seasonNumber' in vid and vid['seasonNumber'] != "" and str(vid['seasonNumber']) != "0" and vid['seasonNumber'] is not None:
					season = str(vid['seasonNumber']).zfill(2)
				if 'episodeNumber' in vid and vid['episodeNumber'] != "" and str(vid['episodeNumber']) != "0" and vid['episodeNumber'] is not None:
					episode = str(vid['episodeNumber']).zfill(2)
				if 'videoType' in vid and vid['videoType'] != "" and vid['videoType'] is not None:
					videoTYPE = vid['videoType']
					if videoTYPE.upper() == 'STANDALONE' and episode == '0':
						pos_SP += 1
				if season != '0' and episode != '0':
					title1 = translation(30626).format(season, episode)
					if videoTYPE.upper() == 'STANDALONE':
						title1 = translation(30627).format(season, episode)
					title2 = title+plus_SUFFIX
					number = 'S'+season+'E'+episode
				else:
					if videoTYPE.upper() == 'STANDALONE':
						episode = str(pos_SP).zfill(2)
						title1 = translation(30628).format(episode)
						title2 = title+'  (Special)'+plus_SUFFIX if not 'Special' in title else title+plus_SUFFIX
						number = 'S00E'+episode
					else:
						title1 = title+plus_SUFFIX
				if 'publishStart' in vid and vid['publishStart'] != "" and vid['publishStart'] is not None and not str(vid['publishStart']).startswith('1970'):
					try:
						startDATES = datetime(*(time.strptime(vid['publishStart'][:19], '%Y{0}%m{0}%dT%H{1}%M{1}%S'.format('-', ':'))[0:6])) # 2019-06-23T14:10:00Z
						LOCALstart = utc_to_local(startDATES)
						startTIMES = LOCALstart.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
						begins =  LOCALstart.strftime('%d{0}%m{0}%Y').format('.')
					except: pass
				if 'publishEnd' in vid and vid['publishEnd'] != "" and vid['publishEnd'] is not None and not str(vid['publishEnd']).startswith('1970'):
					try:
						endDATES = datetime(*(time.strptime(vid['publishEnd'][:19], '%Y{0}%m{0}%dT%H{1}%M{1}%S'.format('-', ':'))[0:6])) # 2019-06-23T14:10:00Z
						LOCALend = utc_to_local(endDATES)
						endTIMES = LOCALend.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
					except: pass
				if 'airDate' in vid and vid['airDate'] != "" and vid['airDate'] is not None and not str(vid['airDate']).startswith('1970'):
					year = vid['airDate'][:4]
				if startTIMES and endTIMES: Note_1 = translation(30629).format(str(startTIMES), str(endTIMES))
				elif startTIMES and endTIMES is None: Note_1 = translation(30630).format(str(startTIMES))
				if 'description' in vid and vid['description'] != "" and vid['description'] is not None:
					Note_2 = cleaning(vid['description']).replace('\n\n\n', '\n\n')
				plot = origSERIE+'[CR]'+Note_1+Note_2
				if 'videoDuration' in vid and vid['videoDuration'] != "" and vid['videoDuration'] is not None:
					duration = get_Time(vid['videoDuration'])
				image = icon
				for attr in DATA['included']:
					if 'attributes' in attr and 'src' in attr['attributes'] and attr['attributes']['src'] != "" and attr['attributes']['src'] is not None:
						if 'id' in attr and attr['id'] is not None and 'video-'+episID in attr['id']:
							image = attr['attributes']['src']
				COMBI_EPISODE.append([number, title1, title2, episID, image, plot, duration, season, episode, genre, year, begins])
	if COMBI_EPISODE:
		if SORTING == '0':
			COMBI_EPISODE = sorted(COMBI_EPISODE, key=lambda b:b[0], reverse=True)
		for number, title1, title2, episID, image, plot, duration, season, episode, genre, year, begins in COMBI_EPISODE:
			if SORTING == '1':
				xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
				xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
				xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_DURATION)
				if episode is not '0':
					xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_EPISODE)
				if begins:
					xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_DATE)
			name = title1.strip() if title2 == "" else title1.strip()+"  "+title2.strip()
			cineType = 'episode' if episode != '0' else 'movie'
			debug_MS("(navigator.listEpisodes) ##### NAME : {0} || IDD : {1} || GENRE : {2} #####".format(str(name), episID, str(genre)))
			debug_MS("(navigator.listEpisodes) ##### IMAGE : {0} || SEASON : {1} || EPISODE : {2} #####".format(image, str(season), str(episode)))
			addLink(name, image, {'mode': 'playVideo', 'url': episID, 'cineType': cineType}, plot, duration, origSERIE, season, episode, genre, year, begins)
	else:
		debug_MS("(navigator.listEpisodes) ##### Keine COMBI_EPISODE-List - Kein Eintrag gefunden #####")
		return dialog.notification(translation(30523), translation(30524).format(origSERIE), icon, 8000)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def playVideo(Xidd):
	debug_MS("(navigator.playVideo) ------------------------------------------------ START = playVideo -----------------------------------------------")
	# NEW Playback = https://eu1-prod.disco-api.com/playback/videoPlaybackInfo/142036?usePreAuth=true
	playURL = '{0}/playback/videoPlaybackInfo/{1}?usePreAuth=true'.format(BASE_API, Xidd)
	content = getUrl(playURL)
	debug_MS("++++++++++++++++++++++++")
	debug_MS("(navigator.playVideo) XXXXX CONTENT : {0} XXXXX".format(str(content)))
	debug_MS("++++++++++++++++++++++++")
	DATA = json.loads(content, object_pairs_hook=OrderedDict)
	videoURL = DATA['data']['attributes']['streaming']['hls']['url']
	log("(navigator.playVideo) StreamURL : "+videoURL)
	listitem = xbmcgui.ListItem(path=videoURL)
	if enableINPUTSTREAM and ADDON_operate('inputstream.adaptive'):
		lic_FILE = DATA['data']['attributes']['protection']['schemes']['clearkey']['licenseUrl']
		lic_URL = getUrl(lic_FILE)
		lic_KEY = json.loads(lic_URL)['keys'][0]['kid']
		debug_MS("(navigator.playVideo) ##### LIC-FILE : {0} || LIC-KEY : {1} #####".format(str(lic_FILE), str(lic_KEY)))
		listitem.setProperty(INPUT_APP, 'inputstream.adaptive')
		listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
		listitem.setProperty('inputstream.adaptive.license_key', lic_KEY)
	xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, listitem)

def listShowsFavs():
	debug_MS("(navigator.listShowsFavs) ------------------------------------------------ START = listShowsFavs -----------------------------------------------")
	xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
	if os.path.exists(channelFavsFile):
		with open(channelFavsFile, 'r') as textobj:
			lines = textobj.readlines()
			for line in lines:
				if line.startswith('###START'):
					part = line.split('###')
					debug_MS("(navigator.listShowsFavs) ### NAME : {0} || URL : {1} || IMAGE : {2} ###".format(str(part[2]), part[3], part[4]))
					addDir(name=part[2], image=part[4], params={'mode': 'listEpisodes', 'url': part[3], 'origSERIE': part[2]}, plot=part[5].replace('#n#', '\n').strip(), FAVdel=True)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def favs(elem):
	modus = elem[elem.find('MODE=')+5:+8]
	TVSe = elem[elem.find('###START'):]
	TVSe = TVSe[:TVSe.find('END###')]
	name = TVSe.split('###')[2]
	url = TVSe.split('###')[3]
	if modus == 'ADD':
		NORMAL = declare_Open(channelFavsFile, 'NORMAL')
		PLUS = declare_Open(channelFavsFile, 'PLUS')
		if os.path.exists(channelFavsFile):
			with PLUS as textobj:
				content = textobj.read()
				if content.find(TVSe) == -1:
					textobj.seek(0,2) # change is here (for Windows-Error = "IOError: [Errno 0] Error") - because Windows don't like switching between reading and writing at same time !!!
					textobj.write(TVSe+'END###\n')
		else:
			with NORMAL as textobj:
				textobj.write(TVSe+'END###\n')
		xbmc.sleep(500)
		dialog.notification(translation(30525), translation(30526).format(name), icon, 8000)
	elif modus == 'DEL':
		with open(channelFavsFile, 'r') as output:
			lines = output.readlines()
		with open(channelFavsFile, 'w') as input:
			for line in lines:
				if url not in line:
					input.write(line)
		xbmc.executebuiltin('Container.Refresh')
		xbmc.sleep(1000)
		dialog.notification(translation(30525), translation(30527).format(name), icon, 8000)

def AddToQueue():
	return xbmc.executebuiltin('Action(Queue)')

def addDir(name, image, params={}, plot=None, addType=0, FAVdel=False):
	u = '{0}?{1}'.format(HOST_AND_PATH, urlencode(params))
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon and not artpic in image:
		liz.setArt({'fanart': image})
	entries = []
	if addType == 1 and FAVdel is False:
		FAVInfos_1 = 'MODE=ADD###START###{0}###{1}###{2}###{3}###END###'.format(params.get('origSERIE'), params.get('url'), image, "" if plot is None else plot.replace('\n', '#n#'))
		entries.append([translation(30651), 'RunPlugin({0}?{1})'.format(HOST_AND_PATH, urlencode({'mode': 'favs', 'url': str(FAVInfos_1)}))])
	if FAVdel is True:
		FAVInfos_2 = 'MODE=DEL###START###{0}###{1}###{2}###{3}###END###'.format(name, params.get('url'), image, plot)
		entries.append([translation(30652), 'RunPlugin({0}?{1})'.format(HOST_AND_PATH, urlencode({'mode': 'favs', 'url': str(FAVInfos_2)}))])
	liz.addContextMenuItems(entries, replaceItems=False)
	return xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=u, listitem=liz, isFolder=True)

def addLink(name, image, params={}, plot=None, duration=None, seriesname=None, season=None, episode=None, genre=None, year=None, begins=None):
	u = '{0}?{1}'.format(HOST_AND_PATH, urlencode(params))
	liz = xbmcgui.ListItem(name)
	info = {}
	info['Season'] = season
	info['Episode'] = episode
	info['Tvshowtitle'] = seriesname
	info['Title'] = name
	info['Tagline'] = None
	info['Plot'] = plot
	info['Duration'] = duration
	if begins is not None:
		info['Date'] = begins
	info['Year'] = year
	info['Genre'] = genre
	info['Studio'] = 'HGTV'
	info['Mpaa'] = None
	info['Mediatype'] = params.get('cineType')
	liz.setInfo(type='Video', infoLabels=info)
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon and not artpic in image:
		liz.setArt({'fanart': image})
	liz.addStreamInfo('Video', {'Duration': duration})
	liz.setProperty('IsPlayable', 'true')
	liz.setContentLookup(False)
	liz.addContextMenuItems([(translation(30654), 'RunPlugin('+HOST_AND_PATH+'?mode=AddToQueue)')])
	return xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=u, listitem=liz)
