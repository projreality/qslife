import wx;

################################################################################
################################## GRAPH DIALOG ################################
################################################################################
class PreferencesDialog(wx.Dialog):

  def __init__(self, options, *args, **kwargs):
    super(PreferencesDialog, self).__init__(*args, **kwargs);

    self.options = options;

    self.create_gui();

    self.SetSize(( 360, 130 ));

  def create_gui(self):
    panel = wx.Panel(self);
    sizer = wx.GridBagSizer(4, 5);

    sizer.Add(wx.StaticText(panel, label="Timezone:"), pos=( 1, 1 ), border=4)

    self.timezone = wx.TextCtrl(panel, size=( 240, -1 ));
    self.timezone.SetValue(str(self.options["timezone"]));
    self.timezone.Bind(wx.EVT_KEY_DOWN, self.onKeyDown);
    sizer.Add(self.timezone, pos=( 1, 2 ), span=( 1, 4 ) );

    ok_button = wx.Button(panel, label="OK");
    ok_button.Bind(wx.EVT_BUTTON, self.onOk);
    sizer.Add(ok_button, pos=( 3, 3 ), span=( 1, 1 ));

    cancel_button = wx.Button(panel, label="Cancel");
    cancel_button.Bind(wx.EVT_BUTTON, self.onCancel);
    sizer.Add(cancel_button, pos=( 3, 4 ), span=( 1, 1 ));

    panel.SetSizer(sizer);

    self.timezone.SetFocus();

  def onKeyDown(self, e):
    key_code = e.GetKeyCode();

    if (key_code == wx.WXK_ESCAPE):
      self.EndModal(wx.ID_CANCEL);
      self.Close();
    elif ((key_code == wx.WXK_RETURN) or (key_code == wx.WXK_NUMPAD_ENTER)):
      self.EndModal(wx.ID_OK);
      self.Close();
    else:
      e.Skip();

  def onOk(self, e):
    self.EndModal(wx.ID_OK);
    self.Close();

  def onCancel(self, e):
    self.EndModal(wx.ID_CANCEL);
    self.Close();

