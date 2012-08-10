import os;
import sys;
import wx;

sys.path.append("lib/olr_import");

import init;

class QSLife(wx.Frame):

################################################################################
################################## CONSTRUCTOR #################################
################################################################################
  def __init__(self, *args, **kwargs):
    super(QSLife, self).__init__(*args, **kwargs);

    # HDFQS
    self.current_file = None;

    # GUI
    self.create_menubar();
    self.gui_miscellaneous_setup();

################################################################################
################################ CREATE MENUBAR ################################
################################################################################
  def create_menubar(self):
    menubar = wx.MenuBar();

################################### FILE MENU ##################################
    # Structure
    menu_file = wx.Menu();
    menu_file_new = menu_file.AppendItem(wx.MenuItem(menu_file, wx.ID_NEW, "&New\tCtrl+N"));
    menu_file_open = menu_file.AppendItem(wx.MenuItem(menu_file, wx.ID_OPEN, "&Open\tCtrl+O"));
    menu_file_exit = menu_file.AppendItem(wx.MenuItem(menu_file, wx.ID_EXIT, "E&xit\tCtrl+Q"));
    menubar.Append(menu_file, "&File");

    # Events
    self.Bind(wx.EVT_MENU, self.onFileNew, menu_file_new);
    self.Bind(wx.EVT_MENU, self.onFileOpen, menu_file_open);
    self.Bind(wx.EVT_MENU, self.onFileExit, menu_file_exit);

################################ FINISH MENUBAR ################################
    self.SetMenuBar(menubar);

################################################################################
############################ GUI MISCELLANEOUS SETUP ###########################
################################################################################
  def gui_miscellaneous_setup(self):
    self.statusbar = self.CreateStatusBar();
    self.SetTitle("-");
    self.Maximize();
    self.Show();

################################################################################
################################### OPEN FILE ##################################
################################################################################
  def open_file(self, path):
    self.current_file = path;
    self.SetTitle(path);

################################################################################
################################# EVENT HANDLERS ###############################
################################################################################

#################################### FILE NEW ##################################
  def onFileNew(self, e):
    dialog = wx.FileDialog(None, "New HDFQS file ...", ".", style=wx.FD_SAVE);
    if (dialog.ShowModal() == wx.ID_OK):
      path = dialog.GetPath();
      if (os.path.exists(path)):
	dialog = wx.MessageDialog(None, "File \"" + path + "\" exists - overwrite?", "Confirm", wx.YES_NO);
	if (dialog.ShowModal() == wx.ID_YES):
	  init.init(path);
	  self.open_file(path);
	  self.statusbar.SetStatusText("Created new file \"" + path + "\"");

################################### FILE OPEN ##################################
  def onFileOpen(self, e):
    dialog = wx.FileDialog(None, "Open HDFQS file ...", ".", style=wx.FD_OPEN);
    if (dialog.ShowModal() == wx.ID_OK):
      path = dialog.GetPath();
      if (os.path.exists(path)):
	self.open_file(path);
	self.SetStatusText("Opened file \"" + path + "\"");
      else:
	wx.MessageBox("File \"" + path + "\" does not exist", "Error", wx.OK | wx.ICON_EXCLAMATION);

################################### FILE EXIT ##################################
  def onFileExit(self, e):
    self.Close();

if (__name__ == "__main__"):
  app = wx.App();
  QSLife(None);
  app.MainLoop();
