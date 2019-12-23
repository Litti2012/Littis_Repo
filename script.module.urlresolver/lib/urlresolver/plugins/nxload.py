"""
    OVERALL CREDIT TO:
        t0mm0, Eldorado, VOINAGE, BSTRDMKR, tknorris, smokdpi, TheHighway

    urlresolver XBMC Addon
    Copyright (C) 2011 t0mm0

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import re
from urlresolver import common
from urlresolver.resolver import UrlResolver, ResolverError
from lib import jsunpack

class NxloadResolver(UrlResolver):
    name = "nxload"
    domains = ["nxload.com"]
    pattern = '(?://|\.)(nxload\.com)/(?:embed-)?([0-9a-zA-Z]+)'

    def __init__(self):
        self.net = common.Net()

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        headers = {'User-Agent': common.RAND_UA}
        html = self.net.http_GET(web_url, headers=headers).content
        try:
            r = re.search('\s+?(eval\(function\(p,a,c,k,e,d\).+)\s+?', html)
            r = jsunpack.unpack(r.group(1))
            r = re.search('src:\\\'([^"]+?)\'', r.replace('\\', ''))
            url = r.group(1)
            return url
        except:
            if html:
                match = re.findall('https(.*?)m3u8', html)[0]
                match = match.split('|')
                for i in range(1, len(match)):
                    if match[i] == 'x':
                        break
                url = 'https://' + match[i+1] + "." + self.domains[0] + "/" + match[i+2] + "/" + match[i+3] + "-" + match[i+4] + "/" + match[i+6] + ".m3u8"

                if match:
                    return url

        raise ResolverError("Video not found")

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id)
