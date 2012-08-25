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
    self.current_config = None;
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
    menu_file_open = menu_file.AppendItem(wx.MenuItem(menu_file, wx.ID_OPEN, "&Open config\tCtrl+O"));
    menu_file_load = menu_file.AppendItem(wx.MenuItem(menu_file, wx.ID_ANY, "&Load HDFQS file\tCtrl+L"));
    menu_file_save = menu_file.AppendItem(wx.MenuItem(menu_file, wx.ID_SAVE, "&Save config\tCtrl+S"));
    menu_file_save_as = menu_file.AppendItem(wx.MenuItem(menu_file, wx.ID_SAVEAS, "Save &As\tCtrl+A"));
    menu_file_exit = menu_file.AppendItem(wx.MenuItem(menu_file, wx.ID_EXIT, "E&xit\tCtrl+Q"));
    menubar.Append(menu_file, "&File");

    # Events
    self.Bind(wx.EVT_MENU, self.onFileNew, menu_file_new);
    self.Bind(wx.EVT_MENU, self.onFileOpen, menu_file_open);
    self.Bind(wx.EVT_MENU, self.onFileLoad, menu_file_load);
    self.Bind(wx.EVT_MENU, self.onFileSave, menu_file_save);
    self.Bind(wx.EVT_MENU, self.onFileSaveAs, menu_file_save_as);
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

    # GraphWindow
    self.graphs = GraphWindow(panel, wx.ID_ANY);

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
    self.graphs.set_clip(temp["clip"]);
    self.graphs.set_current_file(self.current_file);
    self.graphs.set_graph_config(temp["graph_config"]);
    self.graphs.set_num_visible_graphs(temp["num_visible_graphs"]);
    self.graphs.set_time_range(temp["time_range"]);
    self.graphs.set_timezone(temp["timezone"]);
    self.graphs.set_top_graph(temp["top_graph"]);
    self.graphs.update();
    self.current_config = path;

################################################################################
################################## SAVE CONFIG #################################
################################################################################
  def save_config(self, path=None):
    if (path == None):
      path = self.current_config;

    try:
      fd = open(path, "w");
      fd.write("clip = " + repr(self.graphs.get_clip()) + "\n");
      fd.write("current_file = " + repr(self.graphs.get_current_file()) + "\n");
      fd.write("graph_config = " + repr(self.graphs.get_graph_config()) + "\n");
      fd.write("num_visible_graphs = " + repr(self.graphs.get_num_visible_graphs()) + "\n");
      fd.write("time_range = " + repr(self.graphs.get_time_range()) + "\n");
      fd.write("timezone = " + repr(self.graphs.get_timezone()) + "\n");
      fd.write("top_graph = " + repr(self.graphs.get_top_graph()) + "\n");
      fd.close();
      self.SetStatusText("Saved configuration file \"" + path + "\"");
    except IOError:
      wx.MessageBox("Error saving to file \"" + path + "\"!", "Error", wx.OK | wx.ICON_EXCLAMATION);

################################################################################
################################### LOAD FILE ##################################
################################################################################
  def load_file(self, path):
    self.current_file = path;
    self.SetTitle(path);

    self.create_window();
    self.graphs.set_current_file(self.current_file);

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

################################### FILE LOAD ##################################
  def onFileLoad(self, e):
    dialog = wx.FileDialog(None, "Load HDFQS file ...", ".", style=wx.FD_OPEN, wildcard="*.h5");
    if (dialog.ShowModal() == wx.ID_OK):
      path = dialog.GetPath();
      if (os.path.exists(path)):
	self.load_file(path);
	self.graphs.update();
	self.SetStatusText("Loaded file \"" + path + "\"");
      else:
	wx.MessageBox("File \"" + path + "\" does not exist", "Error", wx.OK | wx.ICON_EXCLAMATION);

################################## FILE SAVE ###################################
  def onFileSave(self, e):
    if (self.current_config != None):
      self.save_config();
    else:
      self.onFileSaveAs(e);

################################# FILE SAVE AS #################################
  def onFileSaveAs(self, e):
    dialog = wx.FileDialog(None, "Save configuration file ...", "Save", style=wx.FD_SAVE, wildcard="*.py");
    if (dialog.ShowModal() == wx.ID_OK):
      path = dialog.GetPath();
      if (os.path.exists(path)):
	dialog = wx.MessageDialog(None, "File \"" + path + "\" exists. Overwrite?", "Confirm", wx.YES_NO | wx.ICON_EXCLAMATION);
	if (dialog.ShowModal() != wx.ID_YES):
	  return;
      self.save_config(path);

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
