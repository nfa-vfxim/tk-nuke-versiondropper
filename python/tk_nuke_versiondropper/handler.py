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

import sgtk
import os
import re
import nuke
import nukescripts

# standard toolkit logger
logger = sgtk.platform.get_logger(__name__)


class NukeVersionDropperHandler:
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
        self.published_file_colorspace = self._app.get_setting("published_file_colorspace")
        self.movie_colorspace = self._app.get_setting("movie_colorspace")

        # logging happens via a standard toolkit logger
        logger.debug("Launching Version Dropper Application...")

        # Adding the callback when Nuke initializes
        nukescripts.addDropDataCallback(self.drop_shotgrid_data)

    def drop_shotgrid_data(self, mime_type, text):
        # Making sure data is coming from ShotGrid
        if not mime_type == "text/plain" or not (
            text.startswith("http") and "shotgunstudio" in text
        ):
            return False

        # Retreive ID from url
        def id_check(url, shotgrid_type):
            found_id = re.match(".+%s/(\d+)" % shotgrid_type, url)
            found_id_in_email = re.match(
                ".+entity_id=(\d+).+entity_type=%s" % shotgrid_type, url
            )
            found_id_in_url = re.match(r".+#%s_(\d+)_" % shotgrid_type, url)
            if not found_id and not found_id_in_email and not found_id_in_url:
                return
            try:
                if found_id:
                    return int(found_id.group(1))
                elif found_id_in_email:
                    return int(found_id_in_email.group(1))
                elif found_id_in_url:
                    return int(found_id_in_url.group(1))
            except ValueError:
                return

        # Action when it is a version
        if "Version" in text:
            version_id = id_check(text, "Version")
            self.create_read_node("Version", version_id)
            return True

        if "PublishedFile" in text:
            version_id = id_check(text, "PublishedFile")
            self.create_read_node("PublishedFile", version_id)
            return True

        if "Shot" in text:
            shot_id = id_check(text, "Shot")
            version_id = self.get_latest_version("Shot", shot_id)
            self.create_read_node("Version", version_id)
            return True

        if "Asset" in text:
            asset_id = id_check(text, "Asset")
            version_id = self.get_latest_version("Asset", asset_id)
            self.create_read_node("Version", version_id)
            return True

    def get_latest_version(self, type, id):
        # Getting ShotGrid object
        sg = self.sg

        # Getting latest version created on shot/asset
        filters = [["entity", "is", {"type": type, "id": id}]]
        fields = ["id"]
        sorting = [{"column": "created_at", "direction": "desc"}]
        latest_version = sg.find_one("Version", filters, fields, sorting)
        version_id = latest_version.get("id")

        return version_id

    def create_read_node(self, entity_type, publish_id, parent_type=None):
        # Retrieving ShotGrid data
        sg = self.sg

        columns = [
            "sg_path_to_movie",
            "sg_path_to_frames",
            "sg_first_frame",
            "sg_last_frame",
            "path",
            "sg_frames_colorspace"
        ]
        filters = [["id", "is", publish_id]]

        entity = sg.find_one(entity_type, filters, columns)

        # Use files field if there is any data
        file_path = entity.get("sg_path_to_frames")

        # Otherwise use the movie
        if file_path is None:
            file_path = entity.get("sg_path_to_movie")
            if file_path is None:
                file_path = entity.get("path")
                file_path = file_path.get("local_path")

        # Set initial variable
        file_type = "file"

        if "exr" in file_path:
            start_frame = entity.get("sg_first_frame")
            last_frame = entity.get("sg_last_frame")

            if start_frame is None or last_frame is None:
                folder = os.path.dirname(file_path)
                frame_sequences = self.__get_frame_sequences(folder)

                frame_sequence = frame_sequences[0][0]

                if frame_sequence == file_path:
                    start_frame = int(min(frame_sequences[0][1]))
                    last_frame = int(max(frame_sequences[0][1]))

            file_type = "sequence"

        read_node = nuke.createNode("Read")
        read_node["file"].fromUserText(file_path)
        read_node["localizationPolicy"].setValue(2)

        if file_type == "sequence":
            read_node["first"].setValue(start_frame)
            read_node["last"].setValue(last_frame)

            # We created a custom version field called 'sg_frames_colorspace' allowing us to specify the colorspace
            # to use. If it is not used, we skip to the default colorspace defined in the pipeline config
            colorspace = entity.get("sg_frames_colorspace")
            if colorspace is None:
                if entity_type == "PublishedFile":
                    colorspace = self.published_file_colorspace

                else:
                    colorspace = self.exr_colorspace

            read_node["colorspace"].setValue(colorspace)

        else:
            read_node["colorspace"].setValue(self.movie_colorspace)

    @staticmethod
    def __get_frame_sequences(folder, extensions=None, frame_spec=None):
        """
        Copied from the publisher plugin, and customized to return file sequences with frame lists instead of filenames
        Given a folder, inspect the contained files to find what appear to be
        files with frame numbers.
        :param folder: The path to a folder potentially containing a sequence of
            files.
        :param extensions: A list of file extensions to retrieve paths for.
            If not supplied, the extension will be ignored.
        :param frame_spec: A string to use to represent the frame number in the
            return sequence path.
        :return: A list of tuples for each identified frame sequence. The first
            item in the tuple is a sequence path with the frame number replaced
            with the supplied frame specification. If no frame spec is supplied,
            a python string format spec will be returned with the padding found
            in the file.
            Example::
            get_frame_sequences(
                "/path/to/the/folder",
                ["exr", "jpg"],
                frame_spec="{FRAME}"
            )
            [
                (
                    "/path/to/the/supplied/folder/key_light1.{FRAME}.exr",
                    [<frame_1_framenumber>, <frame_2_framenumber>, ...]
                ),
                (
                    "/path/to/the/supplied/folder/fill_light1.{FRAME}.jpg",
                    [<frame_1_framenumber>, <frame_2_framenumber>, ...]
                )
            ]
        """
        FRAME_REGEX = re.compile(r"(.*)([._-])(\d+)\.([^.]+)$", re.IGNORECASE)

        # list of already processed file names
        processed_names = {}

        # examine the files in the folder
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)

            if os.path.isdir(file_path):
                # ignore subfolders
                continue

            # see if there is a frame number
            frame_pattern_match = re.search(FRAME_REGEX, filename)

            if not frame_pattern_match:
                # no frame number detected. carry on.
                continue

            prefix = frame_pattern_match.group(1)
            frame_sep = frame_pattern_match.group(2)
            frame_str = frame_pattern_match.group(3)
            extension = frame_pattern_match.group(4) or ""

            # filename without a frame number.
            file_no_frame = "%s.%s" % (prefix, extension)


            if file_no_frame in processed_names:
                # already processed this sequence. add the framenumber to the list, later we can use this to determine the framerange
                processed_names[file_no_frame]["frame_list"].append(frame_str)
                continue

            if extensions and extension not in extensions:
                # not one of the extensions supplied
                continue

            # make sure we maintain the same padding
            if not frame_spec:
                padding = len(frame_str)
                frame_spec = "%%0%dd" % (padding,)

            seq_filename = "%s%s%s" % (prefix, frame_sep, frame_spec)

            if extension:
                seq_filename = "%s.%s" % (seq_filename, extension)

            # build the path in the same folder
            seq_path = os.path.join(folder, seq_filename)

            # remember each seq path identified and a list of files matching the
            # seq pattern
            processed_names[file_no_frame] = {
                "sequence_path": seq_path,
                "frame_list": [frame_str],
            }

        # build the final list of sequence paths to return
        frame_sequences = []
        for file_no_frame in processed_names:

            seq_info = processed_names[file_no_frame]
            seq_path = seq_info["sequence_path"]

            frame_sequences.append((seq_path, seq_info["frame_list"]))

        return frame_sequences