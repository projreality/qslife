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

from GraphWindow import GraphWindow;
from GraphWindow import GraphDropTarget;

class QSLife(wx.Frame):

################################################################################
################################## CONSTRUCTOR #################################
################################################################################
  def __init__(self, *args, **kwargs):
    super(QSLife, self).__init__(*args, **kwargs);

    # HDFQS
    self.current_file = None;
    self.time_range = ( 0, 0 );
    self.graph_config = [ ];

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
    menu_file_load = menu_file.AppendItem(wx.MenuItem(menu_file, wx.ID_ANY, "&Load HDFQS file\tCtrl+L"));
    menu_file_exit = menu_file.AppendItem(wx.MenuItem(menu_file, wx.ID_EXIT, "E&xit\tCtrl+Q"));
    menubar.Append(menu_file, "&File");

    # Events
    self.Bind(wx.EVT_MENU, self.onFileNew, menu_file_new);
    self.Bind(wx.EVT_MENU, self.onFileOpen, menu_file_open);
    self.Bind(wx.EVT_MENU, self.onFileLoad, menu_file_load);
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
    self.graphs = GraphWindow(panel, wx.ID_ANY);
    self.graphs.set_timezone(-7);

    # Drag-and-drop
    dt = GraphDropTarget(self.graphs);
    self.graphs.SetDropTarget(dt);
    self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.onDragInit, id=self.tree.GetId());

################################################################################
############################ GUI MISCELLANEOUS SETUP ###########################
################################################################################
  def gui_miscellaneous_setup(self):
    self.statusbar = self.CreateStatusBar();
    self.SetTitle("-");
    self.Maximize();
    self.Show();

################################################################################
################################## OPEN CONFIG #################################
################################################################################
  def open_config(self, path):

    temp = { };
    execfile(path, temp);
    self.current_file = temp["current_file"];
    self.load_file(self.current_file);
    self.graphs.set_current_file(self.current_file);
    self.graphs.set_time_range(temp["time_range"]);
    self.graphs.set_graphs(temp["graph_config"]);
    self.graphs.update();


################################################################################
################################### LOAD FILE ##################################
################################################################################
  def load_file(self, path):
    self.current_file = path;
    self.SetTitle(path);

    self.create_window();
    self.graphs.set_current_file(self.current_file);
    self.graphs.update();

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
################################# EVENT HANDLERS ###############################
################################################################################

#################################### FILE NEW ##################################
  def onFileNew(self, e):
    dialog = wx.FileDialog(None, "New HDFQS file ...", ".", style=wx.FD_SAVE, wildcard="*.h5");
    if (dialog.ShowModal() == wx.ID_OK):
      path = dialog.GetPath();
      if (os.path.exists(path)):
	dialog = wx.MessageDialog(None, "File \"" + path + "\" exists - overwrite?", "Confirm", wx.YES_NO);
	if (dialog.ShowModal() == wx.ID_YES):
	  init.init(path);
	  self.load_file(path);
	  self.statusbar.SetStatusText("Created new file \"" + path + "\"");

################################### FILE OPEN ##################################
  def onFileOpen(self, e):
    dialog = wx.FileDialog(None, "Open QSLife configuration file...", ".", style=wx.FD_OPEN, wildcard="*.py");
    if (dialog.ShowModal() == wx.ID_OK):
      path = dialog.GetPath();
      if (os.path.exists(path)):
	self.open_config(path);
	self.SetStatusText("Opened configuration file \"" + path + "\"");
      else:
	wx.MessageBox("File \"" + path + "\" does not exist", "Error", wx.OK | wx.ICON_EXCLAMATION);

################################### FILE OPEN ##################################
  def onFileLoad(self, e):
    dialog = wx.FileDialog(None, "Load HDFQS file ...", ".", style=wx.FD_OPEN, wildcard="*.h5");
    if (dialog.ShowModal() == wx.ID_OK):
      path = dialog.GetPath();
      if (os.path.exists(path)):
	self.load_file(path);
	self.SetStatusText("Loaded file \"" + path + "\"");
      else:
	wx.MessageBox("File \"" + path + "\" does not exist", "Error", wx.OK | wx.ICON_EXCLAMATION);

################################### FILE EXIT ##################################
  def onFileExit(self, e):
    self.Close();

################################### DRAG INIT ##################################
  def onDragInit(self, e):
    root = self.tree.GetRootItem();
    item = e.GetItem();
    parent = self.tree.GetItemParent(item);
    if ((item == root) or (parent == root)):
      return;
    source = "/" + self.tree.GetItemText(parent) + "/" + self.tree.GetItemText(item);
    tdo = wx.TextDataObject(source);
    tds = wx.DropSource(self.tree);
    tds.SetData(tdo);
    tds.DoDragDrop(True);


if (__name__ == "__main__"):
  app = wx.App();
  QSLife(None);
  app.MainLoop();
