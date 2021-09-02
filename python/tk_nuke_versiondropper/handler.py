# MIT License

# Copyright (c) 2021 Netherlands Film Academy

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Thanks to http://www.nukepedia.com/python/nodegraph/shotgundropper/ for partially the code and explanation :)
# Created by Gilles Vink

import sgtk
import os
import sys
import re
import threading
import nuke
import nukescripts

# standard toolkit logger
logger = sgtk.platform.get_logger(__name__)

class NukeVersionDropperHandler():
    """
    Main application
    """

    def __init__(self):
        """
        Constructor
        """

        # Setting general variables
        self._app = sgtk.platform.current_bundle()
        self.sg = self._app.shotgun

        self.exr_colorspace = self._app.get_setting("exr_colorspace")
        self.movie_colorspace = self._app.get_setting("movie_colorspace")


        # logging happens via a standard toolkit logger
        logger.info("Launching Version Dropper Application...")

        # Adding the callback when Nuke initializes
        nukescripts.addDropDataCallback(self.dropShotGridData)


    def dropShotGridData(self, mimeType, text):
        # Making sure data is coming from ShotGrid
        if not mimeType == 'text/plain' or not (text.startswith( 'http' ) and 'shotgunstudio' in text):
            return False

        # Retreive ID from url
        def idCheck(url, sgType):
            foundID = re.match( '.+%s/(\d+)' % sgType, url )
            foundIDinEmail = re.match( '.+entity_id=(\d+).+entity_type=%s' % sgType, url )
            foundIDinURL = re.match( r'.+#%s_(\d+)_' % sgType, url )
            if not foundID and not foundIDinEmail and not foundIDinURL:
                return
            try:
                if foundID:
                    return int( foundID.group(1) )
                elif foundIDinEmail:
                    return int( foundIDinEmail.group(1) )
                elif foundIDinURL:
                    return int( foundIDinURL.group(1) )
            except ValueError:
                return

        # Action when it is a version
        if 'Version' in text:
            versionID = idCheck(text, 'Version')
            self.createReadNode(versionID)
            return True

        if 'Shot' in text:
            shotID = idCheck(text, 'Shot')
            versionID = self.getLatestVersion('Shot', shotID)
            self.createReadNode(versionID)
            return True

        if 'Asset' in text:
            assetID = idCheck(text, 'Asset')
            versionID = self.getLatestVersion('Asset', assetID)
            self.createReadNode(versionID)
            return True

    def getLatestVersion(self, type, id):
        # Getting ShotGrid object
        sg = self.sg

        # Getting latest version created on shot/asset
        filters = [['entity', 'is', {'type': type, 'id': id}]]
        fields = [
            'id'
            ]
        sorting = [{'column':'created_at','direction':'desc'}]
        latestVersion = sg.find_one('Version', filters, fields, sorting)
        versionID = latestVersion.get('id')

        return versionID


    def createReadNode(self, versionID):
        # Retrieving ShotGrid data
        sg = self.sg

        columns = [ 'sg_path_to_movie', 'sg_first_frame', 'sg_last_frame' ]
        filters = [['id', 'is', versionID]]

        libraryAsset = sg.find_one('Version', filters, columns)

        filePath = libraryAsset.get('sg_path_to_movie')

        fileType = 'file'

        if 'exr' in filePath:
            startFrame = libraryAsset.get('sg_first_frame')
            lastFrame = libraryAsset.get('sg_last_frame')
            fileType = 'sequence'

        readNode = nuke.createNode('Read')
        readNode['file'].fromUserText(filePath)

        if fileType == 'sequence':
            readNode['first'].setValue(startFrame)
            readNode['last'].setValue(lastFrame)
            readNode['colorspace'].setValue(self.exr_colorspace)

        else:
            readNode['colorspace'].setValue(self.movie_colorspace)
