import wx
import pickle

from wx.dataview import TreeListCtrl, EVT_TREELIST_ITEM_CONTEXT_MENU, TL_MULTIPLE
from pubsub import pub

from yamoveset import KNOWN_ENTRIES
from pyxenoverse.gui.file_drop_target import FileDropTarget

CHECK = "\u2714"


class SidePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.code = ''
        self.bac = None
        self.bdm = None
        self.ean = None
        self.cam_ean = None
        self.parent = parent
        self.dirname = ''

        # Name
        self.name = wx.StaticText(self, -1, '(No file loaded)')
        self.font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.name.SetFont(self.font)

        # Buttons
        self.open = wx.Button(self, wx.ID_OPEN, "Load")
        self.copy = wx.Button(self, wx.ID_COPY, "Copy")
        self.copy.Disable()

        # Entry List
        self.entry_list = TreeListCtrl(self, style=TL_MULTIPLE)
        self.entry_list.AppendColumn("BAC Entry")
        self.entry_list.AppendColumn("Copied", width=64)
        self.entry_list.Bind(EVT_TREELIST_ITEM_CONTEXT_MENU, self.on_right_click)
        # self.cdo = wx.CustomDataObject("BDMEntry")

        self.Bind(wx.EVT_BUTTON, self.on_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_BUTTON, self.on_copy, id=wx.ID_COPY)
        self.Bind(wx.EVT_MENU, self.on_copy, id=wx.ID_COPY)
        accelerator_table = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('c'), wx.ID_COPY),
        ])
        self.entry_list.SetAcceleratorTable(accelerator_table)
        self.SetDropTarget(FileDropTarget(self, "load_side_moveset"))

        # Button Sizer
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.open)
        button_sizer.AddSpacer(5)
        button_sizer.Add(self.copy)

        # Use some sizers to see layout options
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.name, 0, wx.CENTER)
        sizer.Add(button_sizer)
        sizer.Add(self.entry_list, 1, wx.ALL | wx.EXPAND, 10)

        # Layout sizers
        self.SetSizer(sizer)
        self.SetAutoLayout(1)

    def on_open(self, _):
        pub.sendMessage('open_side_moveset')

    def build_tree(self):
        self.entry_list.DeleteAllItems()
        root = self.entry_list.GetRootItem()
        for i, entry in enumerate(self.bac.entries):
            if not entry.sub_entries:
                continue
            self.entry_list.AppendItem(
                root, f'{entry.index}: {KNOWN_ENTRIES.get(entry.index, "Unknown")}', data=entry)
        self.copy.Enable()
        self.parent.copied = None
        pub.sendMessage('enable_paste', enabled=False)

    def on_right_click(self, _):
        selected = self.entry_list.GetSelections()
        if not selected:
            return
        menu = wx.Menu()
        menu.Append(wx.ID_COPY)
        self.PopupMenu(menu)
        menu.Destroy()

    def on_copy(self, _):
        selected = self.entry_list.GetSelections()
        if not selected:
            return

        # Deselect all
        item = self.entry_list.GetFirstItem()
        while item.IsOk():
            self.entry_list.SetItemText(item, 1, '')
            item = self.entry_list.GetNextItem(item)
        # Check and add to copied
        copied = []
        for item in selected:
            copied.append(self.entry_list.GetItemData(item))
            self.entry_list.SetItemText(item, 1, CHECK)
        self.parent.copied = pickle.dumps(copied)
        pub.sendMessage('enable_paste', enabled=True)
        pub.sendMessage('set_status_bar', text=f'Copied {len(selected)} entries')
