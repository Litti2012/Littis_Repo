# -*- coding: utf-8 -*-

import sys
import os
import re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import json
import xbmcvfs
import shutil
import socket
import time
from datetime import datetime, timedelta
from collections import OrderedDict
import requests
PY2 = sys.version_info[0] == 2
if PY2:
	from urllib import urlencode, quote_plus, unquote_plus  # Python 2.X
else: 
	from urllib.parse import urlencode, quote_plus, unquote_plus  # Python 3.X
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


global debuging
socket.setdefaulttimeout(40)
HOST_AND_PATH          = sys.argv[0]
ADDON_HANDLE            = int(sys.argv[1])
dialog                                = xbmcgui.Dialog()
addon                                = xbmcaddon.Addon()
addon_id                           = addon.getAddonInfo('id')
addon_name                    = addon.getAddonInfo('name')
addon_version                 = addon.getAddonInfo('version')
addonPath                        = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath                           = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
channelFavsFile               = os.path.join(dataPath, 'HGTV_favourChart.txt')
defaultFanart                   = os.path.join(addonPath, 'fanart.jpg')
icon                                    = os.path.join(addonPath, 'icon.png')
artpic                                 = os.path.join(addonPath, 'resources', 'media', '').encode('utf-8').decode('utf-8')
alppic                                 = os.path.join(addonPath, 'resources', 'media', 'alphabet', '').encode('utf-8').decode('utf-8')
enableINPUTSTREAM     = addon.getSetting('useInputstream') == 'true'
INPUT_APP                       = ('inputstream' if int(xbmc.getInfoLabel('System.BuildVersion')[0:2]) >= 19 else 'inputstreamaddon')
SORTING                           = addon.getSetting('sorting_technique')
useThumbAsFanart         = addon.getSetting('useThumbAsFanart') == 'true'
enableADJUSTMENT       = addon.getSetting('show_settings') == 'true'
DEB_LEVEL                       = (xbmc.LOGNOTICE if addon.getSetting('enableDebug') == 'true' else xbmc.LOGDEBUG)
BASE_API                         = 'https://eu1-prod.disco-api.com'
BASE_URL                        = 'https://de.hgtv.com/'

headers1 = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0', 'Accept-Encoding': 'gzip, deflate'}
xbmcplugin.setContent(ADDON_HANDLE, 'tvshows')

def py2_enc(s, encoding='utf-8'):
	if PY2:
		if not isinstance(s, basestring):
			s = str(s)
		s = s.encode(encoding) if isinstance(s, unicode) else s
	return s

def py2_uni(s, encoding='utf-8'):
	if PY2 and isinstance(s, str):
		s = unicode(s, encoding)
	return s

def py3_dec(d, encoding='utf-8'):
	if not PY2 and isinstance(d, bytes):
		d = d.decode(encoding)
	return d

def translation(id):
	return py2_enc(addon.getLocalizedString(id))

def failing(content):
	log(content, xbmc.LOGERROR)

def debug_MS(content):
	log(content, DEB_LEVEL)

def log(msg, level=xbmc.LOGNOTICE):
	msg = py2_enc(msg)
	return xbmc.log('[{0} v.{1}]{2}'.format(addon_id, addon_version, msg), level)

def declare_Open(FILE, event='NORMAL', err='ignore'):
	if PY2:
		DECLARED = open(FILE, 'a') if event is 'NORMAL' else open(FILE, 'a+')
	else:
		DECLARED = open(FILE, 'a', errors=err) if event is 'NORMAL' else open(FILE, 'a+', errors=err)
	return DECLARED

def get_Time(info, event='SECONDS', roundTo=60):
	secs = int(info/1000)
	mins = (secs+roundTo/2) // roundTo * roundTo /60
	if event is 'SECONDS':
		return "{0:.0f}".format(secs)
	return "{0:.0f}".format(mins)

def ADDON_operate(IDD):
	js_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.GetAddonDetails", "params": {"addonid":"'+IDD+'", "properties": ["enabled"]}, "id":1}')
	if '"enabled":false' in js_query:
		try:
			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.SetAddonEnabled", "params": {"addonid":"'+IDD+'", "enabled":true}, "id":1}')
			failing("(ADDON_operate) ERROR - ERROR - ERROR :\n##### Das benötigte Addon : *{0}* ist NICHT aktiviert !!! #####\n##### Es wird jetzt versucht die Aktivierung durchzuführen !!! #####".format(IDD))
		except: pass
	if '"error":' in js_query:
		dialog.ok(addon_id, translation(30501).format(IDD))
		failing("(ADDON_operate) ERROR - ERROR - ERROR :\n##### Das benötigte Addon : *{0}* ist NICHT installiert !!! #####".format(IDD))
		return False
	if '"enabled":true' in js_query:
		return True

def build_url(query):
	return '{0}?{1}'.format(HOST_AND_PATH, urlencode(query))

def getUrl(url, method='GET', REF='Unknown', headers=None, cookies=None, allow_redirects=False, verify=True, stream=None, data=None):
	response = requests.Session()
	access_token = '00'
	if method == 'GET':
		ACCESS_URL = BASE_API+'/token?realm=hgtv'
		entrance = response.get(ACCESS_URL, headers=headers1, allow_redirects=allow_redirects, verify=verify, stream=stream, timeout=30).text
		access_token = 'Bearer '+json.loads(entrance)['data']['attributes']['token']
		headers2 = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0', 'Authorization': access_token}
		content = response.get(url, headers=headers2, allow_redirects=allow_redirects, verify=verify, stream=stream, timeout=30).text
		content = py2_enc(content)
	elif method == 'POST':
		content = response.post(url, headers=headers, allow_redirects=allow_redirects, verify=verify, data=data, timeout=30)
	return content

def utc_to_local(dt):
	if time.localtime().tm_isdst: return dt - timedelta(seconds=time.altzone)
	else: return dt - timedelta(seconds=time.timezone)

def convert(ID):
	for n in (('227', 'Traumhäuser gestalten'), ('228', 'Wohnträume'), ('229', 'Kochen & Geniessen'), ('230', 'Haus-Flipping'), ('231', 'Zuhause gesucht'), ('261', 'Garten')):
				ID = ID.replace(*n)
	return ID.strip()

def cleaning(text):
	text = py2_enc(text)
	for n in (('&lt;', '<'), ('&gt;', '>'), ('&amp;', '&'), ('&Amp;', '&'), ('&apos;', "'"), ("&quot;", "\""), ("&Quot;", "\""), ("&#x27;", "'"), ('&#34;', '"'), ('&#39;', '\''), ('&#039;', '\''),
				('&#x00c4', 'Ä'), ('&#x00e4', 'ä'), ('&#x00d6', 'Ö'), ('&#x00f6', 'ö'), ('&#x00dc', 'Ü'), ('&#x00fc', 'ü'), ('&#x00df', 'ß'), ('&#xD;', ''), ('\xc2\xb7', '-'),
				('&szlig;', 'ß'), ('&mdash;', '-'), ('&ndash;', '-'), ('&Auml;', 'Ä'), ('&Euml;', 'Ë'), ('&Iuml;', 'Ï'), ('&Ouml;', 'Ö'), ('&Uuml;', 'Ü'), ('&auml;', 'ä'), ('&ouml;', 'ö'), ('&uuml;', 'ü'),
				('&auml;', 'ä'), ('&euml;', 'ë'), ('&iuml;', 'ï'), ('&ouml;', 'ö'), ('&uuml;', 'ü'), ('&#376;', 'Ÿ'), ('&yuml;', 'ÿ'),
				('&agrave;', 'à'), ('&Agrave;', 'À'), ('&aacute;', 'á'), ('&Aacute;', 'Á'), ('&acirc;', 'â'), ('&Acirc;', 'Â'), ('&egrave;', 'è'), ('&Egrave;', 'È'), ('&eacute;', 'é'), ('&Eacute;', 'É'), ('&ecirc;', 'ê'), ('&Ecirc;', 'Ê'),
				('&igrave;', 'ì'), ('&Igrave;', 'Ì'), ('&iacute;', 'í'), ('&Iacute;', 'Í'), ('&icirc;', 'î'), ('&Icirc;', 'Î'), ('&ograve;', 'ò'), ('&Ograve;', 'Ò'), ('&oacute;', 'ó'), ('&Oacute;', 'ó'), ('&ocirc;', 'ô'), ('&Ocirc;', 'Ô'),
				('&ugrave;', 'ù'), ('&Ugrave;', 'Ù'), ('&uacute;', 'ú'), ('&Uacute;', 'Ú'), ('&ucirc;', 'û'), ('&Ucirc;', 'Û'), ('&yacute;', 'ý'), ('&Yacute;', 'Ý'),
				('&atilde;', 'ã'), ('&Atilde;', 'Ã'), ('&ntilde;', 'ñ'), ('&Ntilde;', 'Ñ'), ('&otilde;', 'õ'), ('&Otilde;', 'Õ'), ('&Scaron;', 'Š'), ('&scaron;', 'š'), ('&ccedil;', 'ç'), ('&Ccedil;', 'Ç'),
				('&alpha;', 'a'), ('&Alpha;', 'A'), ('&aring;', 'å'), ('&Aring;', 'Å'), ('&aelig;', 'æ'), ('&AElig;', 'Æ'), ('&epsilon;', 'e'), ('&Epsilon;', 'Ε'), ('&eth;', 'ð'), ('&ETH;', 'Ð'), ('&gamma;', 'g'), ('&Gamma;', 'G'),
				('&oslash;', 'ø'), ('&Oslash;', 'Ø'), ('&theta;', 'θ'), ('&thorn;', 'þ'), ('&THORN;', 'Þ'), ('&bull;', '•'), ('&iexcl;', '¡'), ('&iquest;', '¿'), ('&copy;', '(c)'), ('&nbsp;', ' '), ('&hellip;', '...'), ('\n', ''), ('\t', ''), ('<br />', ' - '),
				("\\'", "'"), ("&rsquo;", "’"), ("&lsquo;", "‘"), ("&sbquo;", "’"), ('&rdquo;', '”'), ('&ldquo;', '“'), ('&bdquo;', '”'), ('&rsaquo;', '›'), ('lsaquo;', '‹'), ('&raquo;', '»'), ('&laquo;', '«')):
				text = text.replace(*n)
	return text.strip()

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

params = parameters_string_to_dict(sys.argv[2])
name = unquote_plus(params.get('name', ''))
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', 'root'))
image = unquote_plus(params.get('image', ''))
page = unquote_plus(params.get('page', '1'))
position = unquote_plus(params.get('position', '0'))
origSERIE = unquote_plus(params.get('origSERIE', ''))
extras = unquote_plus(params.get('extras', 'standard'))
cineType = unquote_plus(params.get('cineType', 'episode'))
