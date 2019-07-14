#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os,codecs
import xbmc,xbmcgui,xbmcaddon,xbmcplugin,urllib,xbmcvfs
from io import BytesIO

def fix_encoding(path):
	if sys.platform.startswith('win'):return unicode(path,'utf-8')
	else:return unicode(path,'utf-8').encode('ISO-8859-1')

addon_ =  xbmcaddon.Addon()
addon_id_ = addon_.getAddonInfo('id')
addon_path_ = fix_encoding(addon_.getAddonInfo('path'))
addon_icon_ = fix_encoding(addon_.getAddonInfo('icon'))
special_path_home_ = fix_encoding(xbmc.translatePath('special://home'))

sys.path.append(os.path.join(addon_path_,'resources','libs'))
import fixetzip as zipfile
import requests

def add_dir(title,url,img,mode):
    u=sys.argv[0]+'?title=' + urllib.quote_plus(title) + '&url=' + urllib.quote_plus(url) + '&img=' + urllib.quote_plus(img) + '&mode=' + str(mode)
    lis=xbmcgui.ListItem(title,iconImage='DefaultFolder.png',thumbnailImage=img)
    lis.setInfo(type='Video',infoLabels={'Title':title} )
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=lis,isFolder=True)

def load_zip_content(url,timeout=30,headers={}):

	try:

		req = requests.get(url,stream=True,timeout=timeout,headers=headers)
		if req.status_code == 200:

			dp = xbmcgui.DialogProgress()
			dp.create('[COLOR blue]DOWNLOAD ZIP CONTENT[/COLOR]','Loading data !','Please wait ...')
			dp.update(0)

			chunk_len= int(0)
			bytes = BytesIO()
			content_bytes_len = int(req.headers.get('Content-Length'))

			while True:

				chunk = req.raw.read(1024)
				if not chunk:break

				chunk_len += len(chunk)
				bytes.write(chunk)
				try:
					percent = min(chunk_len * 100 / content_bytes_len ,100)
					dp.update(percent)
				except:pass

				if dp.iscanceled():
					dp.close()
					sys.exit(0)

			dp.close()
			return bytes

	except Exception as exc:
		xbmcgui.Dialog().ok('[COLOR red]DOWNLOAD ZIP CONTENT ERROR[/COLOR]',str(exc))
		sys.exit(0)

def clean_kodi(dir_path,save_list_array=[]):

	try:

		dp = xbmcgui.DialogProgress()
		dp.create('[COLOR blue]KODI CLEANER[/COLOR]','Clean data !','Please wait ...')
		dp.update(0)

		files_list = []
		counter = int(0)
		files_list = list(os.walk(dir_path,topdown=False,onerror=None,followlinks=True))
		list_len = sum(len(files) for path,dirs,files in files_list)

		for root,dirs,files in files_list:

			for dir in dirs:
				path = os.path.join(root,dir)
				if not any((x in path for x in save_list_array)):

					if os.path.islink(path):
						try:os.unlink(path)
						except:pass
					else:
						try:os.rmdir(path)
						except:pass

			for file in files:
				path = os.path.join(root,file)
				if not any((x in path for x in save_list_array)):

					try:os.unlink(path)
					except:pass

				counter +=1
				try:
					percent = min(counter * 100 / list_len,100)
					dp.update(percent,'Clean data :',path,file)
				except:pass

			if dp.iscanceled():
				dp.close()
				sys.exit(0)

		dp.close()

	except Exception as exc:
		xbmcgui.Dialog().ok('[COLOR red]KODI CLEANER ERROR[/COLOR]',str(exc))
		sys.exit(0)

def extract_zip(bytes,extract_path,zip_pwd=None,save_list_array=[]):

	try:

		dp = xbmcgui.DialogProgress()
		dp.create('[COLOR blue]EXTRACT ZIP[/COLOR]','Unpacking data !','Please wait ...')
		dp.update(0)
	
		zip = zipfile.ZipFile(bytes,mode='r',compression=zipfile.ZIP_STORED,allowZip64=True)

		count = int(0)
		list_len = len(zip.infolist())
		for item in zip.infolist():

			count += 1
			try:
				percent = min(count * 100 / list_len ,100)
				dp.update(percent)
			except:pass

			if not any((x in item.filename for x in save_list_array)):
				try:zip.extract(item,path=extract_path,pwd=zip_pwd)
				except:pass

			if dp.iscanceled():
				zip.close()
				dp.close()
				sys.exit(0)

		zip.close()
		dp.close()

	except Exception as exc:
		xbmcgui.Dialog().ok('[COLOR red]EXTRACT ZIP ERROR[/COLOR]',str(exc))
		sys.exit(0)

def close_kodi(special_path_home):

	if xbmc.getCondVisibility('System.Platform.Windows'):
		try:os.system('@ECHO off')
		except:pass
		try:os.system('TSKKILL Kodi*')
		except:pass
		try:os.system('TASKKILL /IM Kodi* /T /F')
		except:pass

	elif xbmc.getCondVisibility('System.Platform.Android'):
		try: os.system('adb shell kill org.xbmc.kodi')
		except: pass
		try:os.system('adb shell am force-stop org.xbmc.kodi')
		except:pass

		xbmcgui.Dialog().ok('[COLOR red]DANGER ![/COLOR]','[COLOR red]Android system discovered ![/COLOR]','[COLOR red]Force the termination of the program ![/COLOR]','[COLOR red]Do not exit the program via Exit or Quit !\nPress OK ![/COLOR]')
		if 'kodi'in special_path_home.lower():xbmc.executebuiltin('StartAndroidActivity("","android.settings.APPLICATION_DETAILS_SETTINGS","","package:org.xbmc.kodi")')
		else:xbmc.executebuiltin('StartAndroidActivity("","android.settings.APPLICATION_SETTINGS","","")')
		sys.exit(0)

	elif xbmc.getCondVisibility('System.Platform.Linux') or xbmc.getCondVisibility('System.Platform.Darwin'):
		try:os.system('killall Kodi')
		except:pass
		try:os.system('killall -9 Kodi')
		except:pass
		try:os.system('killall -9 kodi.bin')
		except:pass

	elif xbmc.getCondVisibility('System.Platform.OSX'):
		try:os.system('killall AppleTV')
		except:pass
		try:os.system('killall -9 AppleTV')
		except:pass

	elif xbmc.getCondVisibility('System.Platform.Linux.RaspberryPi'):
		try:os.system('sudo initctl stop kodi')
		except:pass

	xbmcgui.Dialog().ok('[COLOR red]DANGER ![/COLOR]','[COLOR red]Program could not be stopped ![/COLOR]','[COLOR red]Force the termination of the program ![/COLOR]','[COLOR red]Do not exit the program via Exit or Quit ![/COLOR]')
	sys.exit(0)

def get_params():
	param=[]
	paramstring=sys.argv[2]
	if len(paramstring)>=2:
		params=sys.argv[2]
		cleanedparams=params.replace('?','')
		if (params[len(params)-1]=='/'):
			params=params[0:len(params)-2]
		pairsofparams=cleanedparams.split('&')
		param={}
		for i in range(len(pairsofparams)):
			splitparams={}
			splitparams=pairsofparams[i].split('=')
			if (len(splitparams))==2:
				param[splitparams[0]]=splitparams[1]                         
		return param
		
params=get_params()

title=None
url=None
img=None
mode=None

try:title=urllib.unquote_plus(params['title'])
except:pass
try:url=urllib.unquote_plus(params['url'])
except:pass
try:img=urllib.unquote_plus(params['img'])
except:pass
try:mode=int(urllib.unquote_plus(params['mode']))
except:pass

if mode == None:

	with codecs.open(os.path.join(addon_path_,'data.txt')) as fi:
		for url in fi:

			if url:

				url = url.strip()
				if not url.endswith('/'):url = url + '/'

				try:
					for file in xbmcvfs.listdir(url)[1]:
						if file.endswith('.zip'):add_dir(file,url+file,url+file.replace('.zip','.png'),1)
				except:pass

elif mode == 1:

	cleaner_save_list = [addon_id_,'service.hsk.archive.installer','Addons27.db','Textures13.db','kodi.log']
	extract_save_list = [addon_id_]

	if addon_.getSetting('save_sources') == 'true':
		cleaner_save_list = cleaner_save_list + ['sources.xml']
		extract_save_list = extract_save_list + ['sources.xml']
	if addon_.getSetting('save_favourites') == 'true':
		cleaner_save_list = cleaner_save_list + ['favourites.xml']
		extract_save_list = extract_save_list + ['favourites.xml']

	bytes = load_zip_content(url)
	xbmc.sleep(500)
	clean_kodi(special_path_home_,save_list_array=cleaner_save_list)
	xbmc.sleep(500)
	extract_zip(bytes,special_path_home_,save_list_array=extract_save_list)
	xbmc.sleep(500)
	close_kodi(special_path_home_)

xbmcplugin.endOfDirectory(handle=int(sys.argv[1]),succeeded=True,updateListing=False,cacheToDisc=False)