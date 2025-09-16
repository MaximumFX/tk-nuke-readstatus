# MIT License

# Copyright (c) 2025 MaximumFX

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

from __future__ import annotations

import os

import nuke


class Icon:
    name: str
    scale: float
    offset_x: float
    offset_y: float

    def __init__(
        self,
        name: str,
        scale: float,
        offset_x: float,
        offset_y: float,
    ):
        self.name = name
        self.scale = scale
        self.offset_x = offset_x
        self.offset_y = offset_y

    @staticmethod
    def from_dict(data: dict):
        return Icon(
            data.get("name"),
            data.get("scale", 0.5),
            data.get("offsetX", 84),
            data.get("offsetY", 0),
        )


class Status:
    icon: Icon
    match_both: bool
    latest: bool = False
    str_include: list[str] = []
    template_match: list = []

    @staticmethod
    def from_dict(data: dict):
        status = Status()
        status.icon = Icon.from_dict(data.get("icon", {}))
        status.match_both = data.get("match_both")
        status.latest = data.get("latest", False)
        status.str_include = data.get("str_include", [])
        status.template_match = data.get("template_match", [])

        return status


class ReadStatus:
    def __init__(self, app):
        """Set global variables"""
        self.app = app
        self.logger = app.logger
        self.current_engine = app.engine
        self.tk = self.current_engine.sgtk
        self.sg = self.current_engine.shotgun
        self.current_context = self.current_engine.context

        self.question_on_missing = self.app.get_setting("question_on_missing")
        self.missing_icon = Icon.from_dict(self.app.get_setting("missing_icon", {}))
        self.statuses = [
            Status.from_dict(status) for status in self.app.get_setting("statuses")
        ]
        self.base_path = self.app.get_setting("icon_base_path")

        # Build the icons
        # self.build_icons()

        breakdown_app = self.current_engine.apps["tk-multi-breakdown2"]
        self.breakdown_manager = (
            breakdown_app.create_breakdown_manager() if breakdown_app else None
        )
        self.breakdown_items = []

        # Apply the icons
        self.update_breakdown()
        self.check_script()

    def update_breakdown(self):
        if self.breakdown_manager:
            self.breakdown_items = self.breakdown_manager.scan_scene()

    def check_script(self):
        """Update all read node's icons in the script"""

        for node in nuke.allNodes(recurseGroups=True):
            self.check_node(node)

    def check_node(self, node):
        """Update a node's icon in the script"""
        file_path = self.__get_file_path(node)

        if file_path is None:
            return

        if file_path != "":
            self.__check_node(node, file_path)
        else:
            node.clearCustomIcon()

    def get_icon_path(self, icon: Icon):
        """
        Construct the icon path

        Args:
            icon (Icon): Icon

        Returns:
            str: Full icon path
        """
        return os.path.join(self.base_path, f"{icon.name}.png")

    def version_up_node(self, max=False):
        """Decrease the currently selected node's version"""
        try:
            # Select current selected node
            node = nuke.selectedNode()

            # Get the file path if the node has one
            file_path = self.__get_file_path(node)
            if file_path is None:
                nuke.message("This node can't be versioned up.")
                return
            if file_path == "":
                nuke.message("This node doesn't have a filepath entered.")
                return

            # If has template match
            templates = self.app.get_setting("versionable")
            if templates:
                for template_key in templates:
                    template = self.tk.templates.get(template_key)
                    fields = template.validate_and_get_fields(file_path)
                    if fields and fields.get("version"):
                        self.logger.debug(f'Versioning up "{node.name()}"')
                        fields["version"] = fields["version"] + 1
                        if max:
                            item = next(
                                (
                                    item
                                    for item in self.breakdown_items
                                    if item.path.replace(os.sep, "/") == file_path
                                ),
                                None,
                            )
                            if item:
                                fields["version"] = (
                                    self.breakdown_manager.get_latest_published_file(
                                        item
                                    ).get("version_number")
                                )

                        new_file_path = template.apply_fields(fields).replace(
                            os.sep, "/"
                        )
                        self.__set_file_path(node, new_file_path)
                    else:
                        self.logger.debug(
                            f'Can\'t version down "{node.name()}", no versionable template defined'
                        )

        # If something went wrong, e.g. no node selected, let user know
        except Exception as error:
            error = str(error)
            if error == "no node selected":
                nuke.message("Please select a node to version up.")
            else:
                nuke.message(str(error))

    def version_down_node(self):
        """Increase the currently selected node's version"""
        try:
            # Select current selected node
            node = nuke.selectedNode()

            # Get the file path if the node has one
            file_path = self.__get_file_path(node)
            if file_path is None:
                nuke.message("This node can't be versioned up.")
                return
            if file_path == "":
                nuke.message("This node doesn't have a filepath entered.")
                return

            # If has template match
            templates = self.app.get_setting("versionable")
            if templates:
                for template_key in templates:
                    template = self.tk.templates.get(template_key)
                    fields = template.validate_and_get_fields(file_path)
                    if fields and fields.get("version"):
                        self.logger.debug(f'Versioning down "{node.name()}"')
                        if fields["version"] == 1:
                            return
                        fields["version"] = fields["version"] - 1
                        new_file_path = template.apply_fields(fields).replace(
                            os.sep, "/"
                        )
                        self.__set_file_path(node, new_file_path)
                    else:
                        self.logger.debug(
                            f'Can\'t version down "{node.name()}", no versionable template defined'
                        )

        # If something went wrong, e.g. no node selected, let user know
        except Exception as error:
            error = str(error)
            if error == "no node selected":
                nuke.message("Please select a node to version down.")
            else:
                nuke.message(str(error))

    def node_to_publish(self):
        """Set the currently selected node's path from a work to a publish path"""
        try:
            # Select current selected node
            node = nuke.selectedNode()

            # Get the file path if the node has one
            file_path = self.__get_file_path(node)
            if file_path is None:
                nuke.message("This node can't be set to publish.")
                return
            if file_path == "":
                nuke.message("This node doesn't have a filepath entered.")
                return

            # If has template match
            mappings = self.app.get_setting("work_publish_mappings")
            if mappings:
                for mapping in mappings:
                    work_template_key = mapping.get("work")
                    publish_template_key = mapping.get("publish")

                    work_template = self.tk.templates.get(work_template_key)
                    publish_template = self.tk.templates.get(publish_template_key)

                    fields = work_template.validate_and_get_fields(file_path)
                    if fields:
                        self.logger.debug(f'Switching "{node.name()}" to publish')
                        print(work_template)
                        print(publish_template)
                        new_file_path = publish_template.apply_fields(fields).replace(
                            os.sep, "/"
                        )
                        self.__set_file_path(node, new_file_path)
                    else:
                        self.logger.debug(
                            f'Can\'t switch "{node.name()}" to publish, no mapping defined'
                        )

        # If something went wrong, e.g. no node selected, let user know
        except Exception as error:
            error = str(error)
            if error == "no node selected":
                nuke.message("Please select a node to switch to publish.")
            else:
                nuke.message(str(error))

    def node_to_work(self):
        """Set the currently selected node's path from a publish to a work path"""
        try:
            # Select current selected node
            node = nuke.selectedNode()

            # Get the file path if the node has one
            file_path = self.__get_file_path(node)
            if file_path is None:
                nuke.message("This node can't be set to publish.")
                return
            if file_path == "":
                nuke.message("This node doesn't have a filepath entered.")
                return

            # If has template match
            mappings = self.app.get_setting("work_publish_mappings")
            if mappings:
                for mapping in mappings:
                    work_template_key = mapping.get("work")
                    publish_template_key = mapping.get("publish")

                    work_template = self.tk.templates.get(work_template_key)
                    publish_template = self.tk.templates.get(publish_template_key)

                    fields = publish_template.validate_and_get_fields(file_path)
                    if fields:
                        self.logger.debug(f'Switching "{node.name()}" to work')
                        print(work_template)
                        print(publish_template)
                        new_file_path = work_template.apply_fields(fields).replace(
                            os.sep, "/"
                        )
                        self.__set_file_path(node, new_file_path)
                    else:
                        self.logger.debug(
                            f'Can\'t switch "{node.name()}" to publish, no mapping defined'
                        )

        # If something went wrong, e.g. no node selected, let user know
        except Exception as error:
            error = str(error)
            if error == "no node selected":
                nuke.message("Please select a node to switch to work.")
            else:
                nuke.message(str(error))

    @staticmethod
    def __get_file_path(node: nuke.Node) -> str | None:
        """
        Get the file path of a node
        Args:
            node (nuke.Node): Nuke node

        Returns:
            str: File path
        """
        if "Write" in node.Class() or "Group" in node.Class():
            return None

        if (
            "Read" in node.Class()
            or "Camera" in node.Class()
            or "Vectorfield" in node.Class()
        ):
            file_key = "file"
            if "Camera4" in node.Class():
                file_key = "file"
            elif "Camera" in node.Class():
                file_key = "file_link"
            elif "Vectorfield" in node.Class():
                file_key = "vfield_file"

            if node.knob(file_key) is None:
                return None

            return node[file_key].value()

        for knob in node.knobs():
            if "file" in knob and isinstance(node[knob].value(), str):
                return node[knob].value()

        return None

    def __set_file_path(self, node: nuke.Node, file_path: str):
        """
        Set the filepath of a node

        Args:
            node (nuke.Node): Nuke node
            file_path (str): File path
        """
        if "Write" in node.Class():
            return

        if (
            "Read" in node.Class()
            or "Camera" in node.Class()
            or "Vectorfield" in node.Class()
        ):
            file_key = "file"
            if "Camera4" in node.Class():
                file_key = "file"
            elif "Camera" in node.Class():
                file_key = "file_link"
            elif "Vectorfield" in node.Class():
                file_key = "vfield_file"

            if node.knob(file_key) is None:
                return None

            node[file_key].setValue(file_path)
            self.__check_node(node, file_path)
            return

        for knob in node.knobs():
            if "file" in knob and isinstance(node[knob].value(), str):
                node[knob].setValue(file_path)
                self.__check_node(node, file_path)

    def __check_node(self, node: nuke.Node, file_path: str):
        """
        Check and update the node's icon

        Args:
            node (nuke.Node): Read node
            file_path (str): File path to check
        """
        found_match = False
        for status in self.statuses:
            # If has string match
            if status.str_include:
                for str_include in status.str_include:
                    if str_include.replace(os.sep, "/") in file_path.replace(
                        os.sep, "/"
                    ):
                        found_match = True

            # If has template match
            if status.template_match:
                for template_key in status.template_match:
                    template = self.tk.templates.get(template_key)
                    if template.validate(file_path):
                        if status.latest:
                            if self.breakdown_manager and self.breakdown_items:
                                item = next(
                                    (
                                        item
                                        for item in self.breakdown_items
                                        if item.path.replace(os.sep, "/") == file_path
                                    ),
                                    None,
                                )
                                if item:
                                    fields = template.get_fields(file_path)
                                    latest_publish = self.breakdown_manager.get_latest_published_file(
                                        item
                                    )
                                    found_match = fields.get(
                                        "version", -1
                                    ) == latest_publish.get("version_number", -1)
                        else:
                            found_match = True

            if found_match:
                self.logger.debug(f"Applying {status.icon.name} icon to {node.name()}")
                node.setCustomIcon(
                    self.get_icon_path(status.icon),
                    status.icon.scale,
                    status.icon.offset_x,
                    status.icon.offset_y,
                )
                return

        if not found_match:
            if self.question_on_missing:
                self.logger.debug(f"Applying missing icon to {node.name()}")
                node.setCustomIcon(
                    self.get_icon_path(self.missing_icon),
                    self.missing_icon.scale,
                    self.missing_icon.offset_x,
                    self.missing_icon.offset_y,
                )
            else:
                self.logger.debug(f"Clearing icon for {node.name()}")
                node.clearCustomIcon()
