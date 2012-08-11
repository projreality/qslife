import matplotlib;
import numpy;
import os;
import sys;
from tables import *;
import wx;

matplotlib.interactive(True);
matplotlib.use("WXAgg");
sys.path.append("lib/olr_import");

import init;
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg;
from matplotlib.figure import Figure;

class QSLife(wx.Frame):

################################################################################
################################## CONSTRUCTOR #################################
################################################################################
  def __init__(self, *args, **kwargs):
    super(QSLife, self).__init__(*args, **kwargs);

    # HDFQS
    self.current_file = None;
    self.time_range = ( 0, 0 );
    self.graphs = [ ];

    # GUI
    self.create_menubar();
    self.window = wx.SplitterWindow(self, wx.ID_ANY, style=wx.SP_3D);
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
################################# CREATE WINDOW ################################
################################################################################
  def create_window(self):
    self.tree = wx.TreeCtrl(self.window, wx.ID_ANY);
    self.tree.AddRoot("/");
    panel = wx.Panel(self.window, style=wx.NO_FULL_REPAINT_ON_RESIZE);
    self.window.SplitVertically(self.tree, panel, 300);

    # Matplotlib
    self.figure = Figure(None, None);
    self.canvas = FigureCanvasWxAgg(panel, -1, self.figure);
    size = tuple(panel.GetClientSize());
    self.canvas.SetSize(size);
    self.figure.set_size_inches(float(size[0])/self.figure.get_dpi(), float(size[1])/self.figure.get_dpi());

    self.update_graphs();

    self.canvas.Bind(wx.EVT_KEY_DOWN, self.onKeyDown);

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

    # Temporary hardwired graphs
    self.time_range = ( 1333504000000L, 1333505000000 );
    self.graphs = [ [ "/Health/hr_nonin3150", "time", "value" ], [ "/Health/ppg_nonin3150", "time", "value" ] ];

    self.create_window();

    # Populate tree
    fd = openFile(path, mode="r");
    root = self.tree.GetRootItem();
    self.tree.SetItemHasChildren(root);
    for item in fd.root:
      tree_item = self.tree.AppendItem(root, item._v_name);
      for subitem in item:
	self.tree.AppendItem(tree_item, subitem._v_name);
    self.tree.Expand(root);
    fd.close();

################################################################################
################################# UPDATE GRAPHS ################################
################################################################################
  def update_graphs(self):
    self.figure.clear();

    num = len(self.graphs);
    fd = openFile(self.current_file, mode="r");
    for i in numpy.arange(num):
      entry = self.graphs[i];
      subplot = self.figure.add_subplot(num, 1, i + 1);
      data = numpy.array([ [ data[entry[1]], data[entry[2]] ] for data in fd.getNode(entry[0]).where("(time > " + str(self.time_range[0]) + ") & (time < " + str(self.time_range[1]) + ")") ]);
      subplot.plot(data[:,0], data[:,1]);
    fd.close();
    self.canvas.draw();

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

#################################### KEY DOWN ##################################
  def onKeyDown(self, e):
    key_code = e.GetKeyCode();

    # Zoom in
    if (key_code == wx.WXK_NUMPAD_ADD):
      gap = self.time_range[1] - self.time_range[0];
      self.time_range = ( self.time_range[0] + gap/4, self.time_range[1] - gap/4 );
      self.update_graphs();
    # Zoom out
    elif (key_code == wx.WXK_NUMPAD_SUBTRACT):
      gap = self.time_range[1] - self.time_range[0];
      self.time_range = ( self.time_range[0] - gap/2, self.time_range[1] + gap/2 );
      self.update_graphs();
    # Move left
    elif ((key_code == wx.WXK_NUMPAD_LEFT) or (key_code == wx.WXK_NUMPAD4) or (key_code == wx.WXK_LEFT)):
      gap = self.time_range[1] - self.time_range[0];
      self.time_range = ( self.time_range[0] - gap/2, self.time_range[1] - gap/2 );
      self.update_graphs();
    # Move right
    elif ((key_code == wx.WXK_NUMPAD_RIGHT) or (key_code == wx.WXK_NUMPAD6) or (key_code == wx.WXK_RIGHT)):
      gap = self.time_range[1] - self.time_range[0];
      self.time_range = ( self.time_range[0] + gap/2, self.time_range[1] + gap/2 );
      self.update_graphs();
    else:
      e.Skip();


if (__name__ == "__main__"):
  app = wx.App();
  QSLife(None);
  app.MainLoop();
