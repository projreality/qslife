# Copyright 2014 Samuel Li
#
# This file is part of QSLife.
#
# QSLife is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# QSLife is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with QSLife.  If not, see <http://www.gnu.org/licenses/>.

import wx;

################################################################################
################################## GRAPH DIALOG ################################
################################################################################
class GraphOptionsDialog(wx.Dialog):

  def __init__(self, parent, config, *args, **kwargs):
    super(GraphOptionsDialog, self).__init__(*args, **kwargs);

    self._parent = parent;

    self.config = config;

    self.create_gui();

    self.SetSize(( 390, 185 ));

  def create_gui(self):
    panel = wx.Panel(self);
    box = wx.StaticBox(panel, label="Graph Options");
    box_sizer = wx.StaticBoxSizer(box, wx.VERTICAL);
    sizer = wx.GridBagSizer(5, 5);

    fields = self._parent.hdfqs.get_fields(self.config["node"]);
    fields.remove("time");
    fields.sort();

    if ("new" in self.config):
      if ("value" in fields):
        self.config["value"] = "value";
      else:
        self.config["value"] = fields[0];
      self.config["valid"] = "";
      self.config["yscale"] = ( 0, 1 );

    sizer.Add(wx.StaticText(panel, label="Value field"), pos=( 0, 0 ), flag=wx.LEFT | wx.TOP, border=4);
    self.value_field = wx.Choice(panel);
    self.value_field.SetItems(fields);
    self.value_field.SetStringSelection(self.config["value"]);
    sizer.Add(self.value_field, pos=( 0, 1 ), border=4);


    sizer.Add(wx.StaticText(panel, label="Valid condition"), pos=( 1, 0 ), border=4)

    self.masking = wx.TextCtrl(panel, size=( 250, -1 ));
    self.masking.SetValue(self.config["valid"]);
    self.masking.Bind(wx.EVT_KEY_DOWN, self.onKeyDown);
    sizer.Add(self.masking, pos=( 1, 1 ), span=( 1, 3) );

    sizer.Add(wx.StaticText(panel, label="Y min"), pos=( 2, 0 ), border=4);

    self.ymin = wx.TextCtrl(panel, size=( 75, -1 ));
    self.ymin.SetValue(str(self.config["yscale"][0]));
    self.ymin.Bind(wx.EVT_KEY_DOWN, self.onKeyDown);
    sizer.Add(self.ymin, pos=( 2, 1 ), span=( 1, 1 ));

    sizer.Add(wx.StaticText(panel, label="Y max"), pos=( 3, 0 ), flag=wx.LEFT | wx.TOP, border=4);

    self.ymax = wx.TextCtrl(panel, size=( 75, -1 ));
    self.ymax.SetValue(str(self.config["yscale"][1]));
    self.ymax.Bind(wx.EVT_KEY_DOWN, self.onKeyDown);
    sizer.Add(self.ymax, pos=( 3, 1 ), span=( 1, 1 ));

    ok_button = wx.Button(panel, label="OK");
    ok_button.Bind(wx.EVT_BUTTON, self.onOk);
    sizer.Add(ok_button, pos=( 4, 2 ), span=( 1, 1 ));

    cancel_button = wx.Button(panel, label="Cancel");
    cancel_button.Bind(wx.EVT_BUTTON, self.onCancel);
    sizer.Add(cancel_button, pos=( 4, 3 ), span=( 1, 1 ));

    box_sizer.Add(sizer);

    panel.SetSizer(box_sizer);

    self.masking.SetFocus();

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

