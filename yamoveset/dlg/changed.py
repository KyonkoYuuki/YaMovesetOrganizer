import wx
from wx.lib.scrolledpanel import ScrolledPanel
from pyxenoverse.bac.types.animation import Animation
from pyxenoverse.bac.types.camera import Camera
from pyxenoverse.bac.types.hitbox import Hitbox


class ChangedDialog(wx.Dialog):
    def __init__(self, parent, changed_values, *args, **kw):
        super().__init__(parent, *args, **kw)
        self.SetTitle("Combo info")
        sizer = wx.BoxSizer(wx.VERTICAL)
        font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        scrolled_panel = ScrolledPanel(self, size=(400, 600))
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        for item_type, values in changed_values.items():
            label = wx.StaticText(scrolled_panel, -1, item_type.__name__)
            label.SetFont(font)
            panel_sizer.AddSpacer(10)
            panel_sizer.Add(label, 0, wx.CENTER)
            panel_sizer.AddSpacer(10)

            grid_sizer = wx.FlexGridSizer(rows=len(values) + 1, cols=4, hgap=10, vgap=10)
            grid_sizer.Add(wx.StaticText(scrolled_panel, -1, 'BAC Entry'))
            if item_type == Animation:
                grid_sizer.Add(wx.StaticText(scrolled_panel, -1, f'{parent.code}.ean'))
                grid_sizer.Add(wx.StaticText(scrolled_panel, -1, ''))
                grid_sizer.Add(wx.StaticText(scrolled_panel, -1, f'{parent.parent.side_panel.code}.ean'))
            elif item_type == Hitbox:
                grid_sizer.Add(wx.StaticText(scrolled_panel, -1, f'{parent.code}_PLAYER.bdm'))
                grid_sizer.Add(wx.StaticText(scrolled_panel, -1, ''))
                grid_sizer.Add(wx.StaticText(scrolled_panel, -1, f'{parent.parent.side_panel.code}_PLAYER.bdm'))
            elif item_type == Camera:
                grid_sizer.Add(wx.StaticText(scrolled_panel, -1, f'{parent.code}.cam.ean'))
                grid_sizer.Add(wx.StaticText(scrolled_panel, -1, ''))
                grid_sizer.Add(wx.StaticText(scrolled_panel, -1, f'{parent.parent.side_panel.code}.cam.ean'))
            else:
                raise(TypeError(f'Unsupported type: {item_type.__name__}'))
            for val in values:
                grid_sizer.Add(wx.StaticText(scrolled_panel, -1, val[0]))
                grid_sizer.Add(wx.StaticText(scrolled_panel, -1, val[1]))
                grid_sizer.Add(wx.StaticText(scrolled_panel, -1, '<-'))
                grid_sizer.Add(wx.StaticText(scrolled_panel, -1, val[2]))
            panel_sizer.Add(grid_sizer, 0, wx.ALL, 10)
        scrolled_panel.SetSizer(panel_sizer)
        scrolled_panel.SetupScrolling()

        sizer.Add(scrolled_panel, 0, wx.ALL | wx.EXPAND, 10)
        sizer.Add(self.CreateButtonSizer(wx.OK), 0, wx.CENTER | wx.ALL, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.CenterOnParent()
        self.Layout()
