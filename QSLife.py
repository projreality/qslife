import wx;

class QSLife(wx.Frame):

################################################################################
################################ CONSTRUCTOR ###################################
################################################################################
  def __init__(self, *args, **kwargs):
    super(QSLife, self).__init__(*args, **kwargs);
    self.create_menubar();
    self.Show();

################################################################################
############################### CREATE MENUBAR #################################
################################################################################
  def create_menubar(self):
    menubar = wx.MenuBar();

################################# FILE MENU ####################################
    # Structure
    menu_file = wx.Menu();
    menu_file_exit = menu_file.AppendItem(wx.MenuItem(menu_file, wx.ID_EXIT, "E&xit\tCtrl+Q"));
    menubar.Append(menu_file, "&File");

    # Events
    self.Bind(wx.EVT_MENU, self.onFileExit, menu_file_exit);

############################## FINISH MENUBAR ##################################
    self.SetMenuBar(menubar);

################################################################################
############################### EVENT HANDLERS #################################
################################################################################

################################# FILE EXIT ####################################
  def onFileExit(self, e):
    self.Close();

if (__name__ == "__main__"):
  app = wx.App();
  QSLife(None);
  app.MainLoop();
