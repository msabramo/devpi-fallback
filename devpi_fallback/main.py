from __future__ import print_function
from __future__ import unicode_literals

import os

from requests.exceptions import HTTPError

from devpi_server.log import threadlog
import devpi_server
from devpi_common.request import new_requests_session
from devpi_server.extpypi import IndexParser, URL

server_version = devpi_server.__version__
session = new_requests_session(agent=("server", server_version))


def devpiserver_get_projectname(stage, name):
    print('*** devpiserver_get_projectname: stage.name=%r; name=%r'
          % (stage.name, name))
    try:
        cheeseprism_data = get_data_from_cheeseprism(name)
    except HTTPError:
        # Try querying on normalized (lowercased) name
        try:
            cheeseprism_data = get_data_from_cheeseprism(name.lower())
        except HTTPError:
            return None
        else:
            return cheeseprism_data[0]['name']
    else:
        return cheeseprism_data[0]['name']


def devpiserver_list_versions(stage, projectname):
    cheeseprism_data = get_data_from_cheeseprism(projectname)
    return [x['version'] for x in cheeseprism_data]


def devpiserver_get_versiondata(stage, projectname, version):
    cheeseprism_data = get_data_from_cheeseprism(projectname)

    for versiondata in cheeseprism_data:
        if versiondata['version'] == version:
            result = dict(versiondata)
            result['+links'] = get_links_list(versiondata)
            return result


def get_links_list(versiondata):
    url = os.path.join('+fetch', versiondata['filename'])
    return [{'href': url, 'rel': 'releasefile'}]


# def devpiserver_on_project_not_found(stage, projectname, redirect):
#     print('*** devpiserver_on_project_not_found: '
#           'stage.name=%r; projectname=%r; redirect=%r'
#           % (stage.name, projectname, redirect))
#     upstream_url = get_upstream_url(projectname)
#     if upstream_url:
#         releaselinks = get_releaselinks(projectname, upstream_url)
#         print('*** releaselinks = %r' % releaselinks)
#         if False:
#             upload_releaselinks(stage, projectname, releaselinks)
#         redirect(upstream_url)


from devpi_server.model import ELink

def devpiserver_get_releaselinks(stage, projectname):
    print('*** devpiserver_get_releaselinks: stage.name=%r; projectname=%r'
          % (stage.name, projectname))

    cp_data = get_data_from_cheeseprism(projectname)

    releaselinks = [get_elink(stage, projectname, cp_entry)
                    for cp_entry in cp_data]
    print('*** devpiserver_get_releaselinks: releaselinks = %r' % releaselinks)
    return releaselinks


def get_elink(stage, projectname, cp_entry):
    entrypath = os.path.join(stage.name, '+f', cp_entry['filename'])
    hash_spec = 'md5=%s' % cp_entry['md5']

    return ELink(
        projectname=projectname, version=cp_entry['version'],
        linkdict={'entrypath': entrypath,
                  'hash_spec': hash_spec},
        filestore=None)


# def get_releaselinks_from_upstream_url(projectname, upstream_url):
#     response = session.get(upstream_url)
#     html = response.text
#     index_parser = IndexParser(projectname)
#     index_parser.parse_index(URL(upstream_url), html)
#     return index_parser.releaselinks


def get_data_from_cheeseprism(projectname):
    cheeseprism_json_url = 'http://packages.corp.surveymonkey.com/index/%s/index.json' % projectname
    # import pdb; pdb.set_trace()
    response = session.get(cheeseprism_json_url)
    response.raise_for_status()
    return response.json()


def copy_from_cheeseprism(stage, projectname, cheeseprism_data):
    # import pdb; pdb.set_trace()
    for entry in cheeseprism_data:
        # Entries look like this:
        #
        # {u'atime': 1389285188.4678197,
        #  u'ctime': 1389285188.4678197,
        #  u'filename': u'smlib.web-1.4.tar.gz',
        #  u'md5': u'92a35b18e5aede3534247aa6824d948f',
        #  u'mtime': 1389223709.0,
        #  u'name': u'smlib.web',
        #  u'size': 8660,
        #  u'version': u'1.4'}
        import pprint; pprint.pprint(entry)
        # basename_without_extension = link.basename
        # version = link.basename.split('-', 1)
        # url_str = link.url
        # print('*** url_str = %r' % url_str)
        # ...
        version = entry['version']
        link = stage.store_releasefile(
            projectname, version,
            content.filename, content.file.read())


def get_upstream_url(projectname):
    return 'http://packages.corp.surveymonkey.com/index/%s' % projectname
