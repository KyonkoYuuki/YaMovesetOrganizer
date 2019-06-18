import wx


COMBO_MSG = '''
# Light Attacks

Base Combo = LC  LC  LC  LC  LC  LC  LC  LC  LC  (keys )
Base Combo = 300 301 302 303 304 340 341 342 343 (bac entries )

Combo 1 = LC  LC  LC  LC  LC  RC  RC  RC
Combo 1 = 300 301 302 303 304 310 311 312

Combo 2 = LC  RC(HOLD)                     RC 
Combo 2 = 300 320(70%),321(85%),322(100%)  325
_______________________________________________________________

# Strong Attacks

Combo 1 = RC  RC  RC  RC  RC  (keys )
Combo 1 = 330 335 336 337 338 (bac entries )

Combo 2 = RC  LC  LC  LC  LC
Combo 2 = 330 340 341 342 343

Combo 3 = RC  LC  RC  LC  RC
Combo 3 = 330 340 350 351 352
_______________________________________________________________

'''


class ComboInfoDialog(wx.Dialog):
    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw, style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)
        self.SetTitle("Combo info")
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.CreateTextSizer(COMBO_MSG), 0, wx.ALL, 10)
        self.sizer.Add(self.CreateButtonSizer(wx.OK), 0, wx.CENTER | wx.ALL, 10)

        self.SetSizer(self.sizer)
        self.sizer.Fit(self)

        self.CenterOnParent()
        self.SetAutoLayout(0)
