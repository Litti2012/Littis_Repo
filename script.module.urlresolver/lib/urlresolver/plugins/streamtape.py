'''
Plugin for URLResolver
#an Check 16.11.2020
#Ka Check 2020-06-30
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

import re
from urlresolver.plugins.lib import helpers
from urlresolver import common
from urlresolver.resolver import UrlResolver, ResolverError

class StreamtapeResolver(UrlResolver):
    name = "streamtape"
    domains = ["streamtape.com"]
    pattern = r'(?://|\.)(streamtape\.com)/(?:e|v)/([0-9a-zA-Z]+)'

    def __init__(self):
        self.net = common.Net()

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        headers = {'User-Agent': common.FF_USER_AGENT,
                   'Referer': 'https://{0}/'.format(host)}
        r = self.net.http_GET(web_url, headers=headers)
        src = re.search(r"innerHTML'.+?'([^']+)", r.content)
        if src:
            src_url = 'https:' + src.group(1) if src.group(1).startswith('//') else src.group(1)
            src_url += '&stream=1'
            return helpers.get_redirect_url(src_url, headers) + helpers.append_headers(headers)
        raise ResolverError('Video cannot be located.')

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, template='https://{host}/e/{media_id}')
