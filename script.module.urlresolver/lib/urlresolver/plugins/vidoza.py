"""
    Kodi urlresolver plugin
    Copyright (C) 2016  script.module.urlresolver

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
from lib import helpers
from urlresolver import common
from urlresolver.resolver import UrlResolver, ResolverError


class VidozaResolver(UrlResolver):
    name = 'vidoza'
    domains = ['vidoza.net']
    pattern = '(?://|\.)(vidoza\.net)/(?:embed-)?([0-9a-zA-Z]+)'

    def __init__(self):
        self.net = common.Net()

    def get_media_url(self, host, media_id):       
        web_url = self.get_url(host, media_id)
        headers = {'User-Agent': common.RAND_UA}
        html = self.net.http_GET(web_url, headers=headers).content
        sources = helpers.scrape_sources(html, patterns=[r'''["']?\s*(?:file|src)\s*["']?\s*[:=,]?\s*["'](?P<url>[^"']+)(?:[^}>\]]+)["']?\s*res\s*["']?\s*[:=]\s*["']?(?P<label>[^"',]+)'''], generic_patterns=False)
        if sources:
            return helpers.pick_source(sources) + helpers.append_headers(headers)

        raise ResolverError('Video cannot be located.')

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, template='https://{host}/embed-{media_id}.html')