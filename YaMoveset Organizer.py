#!/usr/local/bin/python3.6
from collections import defaultdict
import os
from pathlib import Path
import re
import sys
import traceback

from pubsub import pub
import wx
from wx.lib.dialogs import MultiMessageDialog

from pyxenoverse.bac import BAC
from pyxenoverse.bdm import BDM
from pyxenoverse.ean import EAN
from yamoveset.panels.main import MainPanel
from yamoveset.panels.side import SidePanel
from yamoveset.dlg.combo import ComboInfoDialog

VERSION = '0.2.4'


class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        sys.excepthook = self.exception_hook
        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH)
        self.copied = None

        # A "-1" in the size parameter instructs wxWidgets to use the default size.
        # In this case, we select 200px width and the default height.
        wx.Frame.__init__(self, parent, title=title, size=(1200, 800))
        self.statusbar = self.CreateStatusBar()  # A Statusbar in the bottom of the window

        # Setting up the menu.
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_ABOUT)
        file_menu.Append(wx.ID_EXIT)

        help_menu = wx.Menu()
        help_menu.Append(wx.ID_HELP, '&Combo info\tF1')

        # Creating the menubar.
        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, "&File")  # Adding the "filemenu" to the MenuBar
        menu_bar.Append(help_menu, "&Help")  # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menu_bar)  # Adding the MenuBar to the Frame content.

        # Publisher
        pub.subscribe(self.open_main_moveset, 'open_main_moveset')
        pub.subscribe(self.load_main_moveset, 'load_main_moveset')
        pub.subscribe(self.open_side_moveset, 'open_side_moveset')
        pub.subscribe(self.load_side_moveset, 'load_side_moveset')
        pub.subscribe(self.save_moveset, 'save_moveset')
        pub.subscribe(self.set_status_bar, 'set_status_bar')

        # Events
        self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.on_help, id=wx.ID_HELP)
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)
        accelerator_table = wx.AcceleratorTable([
            (wx.ACCEL_NORMAL, wx.WXK_F1, wx.ID_HELP),
        ])
        self.SetAcceleratorTable(accelerator_table)

        # Panels
        self.main_panel = MainPanel(self)
        self.side_panel = SidePanel(self)

        # Sizer
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.main_panel, 1, wx.ALL|wx.EXPAND)
        self.sizer.Add(self.side_panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.help = ComboInfoDialog(self)

        self.sizer.Layout()
        self.Show()

    def exception_hook(self, e, value, trace):
        with MultiMessageDialog(self, '', 'Error', ''.join(traceback.format_exception(e, value, trace)), wx.OK) as dlg:
            dlg.ShowModal()

    def on_about(self, _):
        # Create a message dialog box
        with wx.MessageDialog(self, " Yet another Moveset Organizer v{} by Kyonko Yuuki".format(VERSION),
                              "About YaMoveset Organizer", wx.OK) as dlg:
            dlg.ShowModal() # Shows it

    def on_help(self, _):
        self.help.Show()

    def on_exit(self, _):
        self.Close(True)  # Close the frame.

    def file_not_found_dialog(self, filetype, skip=False):
        msg = f'No Valid {filetype} file found'
        if skip:
            msg += ' but skipping anyway.\n' \
                   'WARNING: May be unable to copy/paste certain moves moves that require this file'
        with wx.MessageDialog(self, msg, 'Warning') as dlg:
            dlg.ShowModal()

    def file_invalid_dialog(self, path, filetype, skip=False):
        msg = f'{path.name} is not a valid {filetype}'
        if skip:
            msg += ' but skipping anyway.\n' \
                   'WARNING: May be unable to copy/paste certain moves moves that require this file'
        with wx.MessageDialog(self, msg, 'Warning') as dlg:
            dlg.ShowModal()

    def open_file_dialog(self, panel):
        with wx.DirDialog(self, 'Choose directory with moveset', panel.dirname,
                          wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            panel.dirname = dlg.GetPath()
            self.open_folder(panel)

    def open_folder(self, panel):
        # Attempt to get Character Code
        bac_files = Path(panel.dirname).glob('*_PLAYER.bac')
        character_codes = []
        for f in bac_files:
            match = re.match(r'(\w{3})_PLAYER.bac', f.name)
            if match:
                character_codes.append(match[1])

        # Did we get Character codes
        if not character_codes:
            self.file_not_found_dialog('BAC')
            return

        # If we had more then one, pick one
        if len(character_codes) > 1:
            with wx.SingleChoiceDialog(
                    self, 'Which character do you want to use?', 'Found multiple characters', character_codes) as dlg:
                if dlg.ShowModal() != wx.ID_OK:
                    return
                code = dlg.GetStringSelection()
        else:
            code = character_codes[0]

        self.load_files(panel.dirname, code, panel)

    def open_file(self, filename, dirname, panel):
        path = Path(os.path.join(dirname, filename))
        if path.is_dir():
            panel.dirname = str(path)
            self.open_folder(panel)
            return

        match = re.match(r'(\w{3})_?.*[.].*', filename)
        panel.dirname = dirname
        if not match:
            with wx.MessageDialog(self, f'No valid character code found') as dlg:
                dlg.ShowModal()
            return
        self.load_files(dirname, match[1], panel)

    def load_single_file(self, path, obj_class, filetype=None, skip=False):
        if not filetype:
            filetype = obj_class.__name__
        if not path.is_file():
            self.file_not_found_dialog(filetype, skip)
            return None

        new_obj = obj_class()

        if not new_obj.load(str(path)):
            self.file_invalid_dialog(path, filetype, skip)
            return None

        return new_obj

    def load_files(self, path, code, panel):
        new_bac = self.load_single_file(Path(os.path.join(path, f'{code}_PLAYER.bac')), BAC)
        if not new_bac:
            return
        new_ean = self.load_single_file(Path(os.path.join(path, f'{code}.ean')), EAN)
        if not new_ean:
            return

        # Optional
        new_bdm = self.load_single_file(Path(os.path.join(path, f'{code}_PLAYER.bdm')), BDM, skip=True)
        new_cam_ean = self.load_single_file(
            Path(os.path.join(path, f'{code}.cam.ean')), EAN, filetype='CAM.EAN', skip=True)

        panel.code = code
        panel.bac = new_bac
        panel.bdm = new_bdm
        panel.ean = new_ean
        panel.cam_ean = new_cam_ean
        panel.build_tree()
        panel.name.SetLabel(code)
        panel.Layout()
        self.main_panel.links = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        self.statusbar.SetStatusText(f'Loaded {code} moveset')

    def open_main_moveset(self):
        self.open_file_dialog(self.main_panel)

    def load_main_moveset(self, filename, dirname):
        self.open_file(filename, dirname, self.main_panel)

    def open_side_moveset(self):
        self.open_file_dialog(self.side_panel)

    def load_side_moveset(self, filename, dirname):
        self.open_file(filename, dirname, self.side_panel)

    def save_moveset(self):
        with wx.DirDialog(self, 'Choose directory to save moveset to', self.main_panel.dirname,
                          wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            self.main_panel.dirname = path = dlg.GetPath()

        with wx.TextEntryDialog(self, 'Enter 3-character code to save this as', value=self.main_panel.code) as dlg:
            dlg.SetMaxLength(3)
            while True:
                if dlg.ShowModal() != wx.ID_OK:
                    return
                code = dlg.GetValue()
                if code.isalnum():
                    break
                with wx.MessageDialog(self, 'Character code can only consist of alphanumeric values') as warn:
                    warn.ShowModal()

        if self.main_panel.bac is not None:
            self.main_panel.bac.save(os.path.join(path, f'{code}_PLAYER.bac'))
        if self.main_panel.bdm is not None:
            self.main_panel.bdm.save(os.path.join(path, f'{code}_PLAYER.bdm'))
        if self.main_panel.ean is not None:
            self.main_panel.ean.save(os.path.join(path, f'{code}.ean'))
        if self.main_panel.cam_ean is not None:
            self.main_panel.cam_ean.save(os.path.join(path, f'{code}.cam.ean'))

        msg = f'Saved {code} moveset successfully!'
        self.statusbar.SetStatusText(msg)
        with wx.MessageDialog(self, msg, '', wx.OK) as dlg:
            dlg.ShowModal()

    def set_status_bar(self, text):
        self.statusbar.SetStatusText(text)


if __name__ == '__main__':
    app = wx.App(False)
    frame = MainWindow(None, "YaMoveset Organizer v" + VERSION)
    app.MainLoop()
