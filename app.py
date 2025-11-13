# MIT License
#
# Copyright (c) 2024 MaximumFX
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sgtk
import nuke


class TkNukeReadStatus(sgtk.platform.Application):
    """
    A Shotgun Toolkit app which adds status indicators to Nuke Read nodes.
    """

    def init_app(self):
        """
        Initialize the app.
        """
        tk_nuke_readstatus = self.import_module("tk_nuke_readstatus")
        self.handler = tk_nuke_readstatus.ReadStatus(self)

        self.engine.register_command(
            "Check all nodes",
            lambda: self.check_script(),
            {
                "short_name": "check_script",
                "icon": "Refresh.png",
                "context": self.context,
            },
        )
        self.engine.register_command(
            "Version up",
            lambda: self.version_up_node(),
            {"short_name": "version_up", "icon": "arrow_up.png", "hotkey": "alt+up"},
        )
        self.engine.register_command(
            "Version down",
            lambda: self.version_down_node(),
            {
                "short_name": "version_down",
                "icon": "arrow_down.png",
                "hotkey": "alt+down",
            },
        )
        self.engine.register_command(
            "Max version",
            lambda: self.version_up_max_node(),
            {
                "short_name": "version_up_max",
                "icon": "arrow_up.png",
                "hotkey": "alt+shift+up",
            },
        )
        self.engine.register_command(
            "Switch from work to published",
            lambda: self.node_to_publish(),
            {"short_name": "to_pub", "icon": "LoadParent.png", "hotkey": "alt+right"},
        )
        self.engine.register_command(
            "Switch from published to work",
            lambda: self.node_to_work(),
            {
                "short_name": "to_work",
                "icon": "LoadParentPartly.png",
                "hotkey": "alt+left",
            },
        )

        self._script_is_loading = True
        self._register_nuke_callbacks()

    def destroy_app(self):
        nuke.removeOnCreate(self._on_node_created)
        nuke.removeOnScriptLoad(self._on_script_load)
        nuke.removeOnScriptClose(self._on_script_close)

    def check_this_node(self):
        self.check_node(nuke.thisNode())

    def check_script(self):
        """Check the read nodes in the currently open script"""
        self.handler.check_script()

    def check_node(self, node):
        """Update a node's icon in the script"""
        self.handler.update_breakdown()
        self.handler.check_node(node)

    def version_up_node(self):
        """Version up the currently selected read node"""
        self.handler.version_up_node()

    def version_down_node(self):
        """Version down the currently selected read node"""
        self.handler.version_down_node()

    def version_up_max_node(self):
        """Version up the currently selected read node to the latest"""
        self.handler.version_up_node(True)

    def node_to_publish(self):
        """Version down the currently selected read node"""
        self.handler.node_to_publish()

    def node_to_work(self):
        """Version up the currently selected read node"""
        self.handler.node_to_work()

    def _register_nuke_callbacks(self):
        """Register callbacks used by the app."""
        nuke.addOnCreate(self._on_node_created)
        nuke.addOnScriptLoad(self._on_script_load)
        nuke.addOnScriptClose(self._on_script_close)

    def _on_node_created(self):
        """Handle node creation after the script has finished loading."""
        if self._script_is_loading:
            return

        self.check_this_node()

    def _on_script_load(self):
        """Mark the end of script loading and refresh the read nodes."""
        self._script_is_loading = False
        self.check_script()

    def _on_script_close(self):
        """Mark the script as loading before a new file is opened."""
        self._script_is_loading = True
