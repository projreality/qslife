import matplotlib;
import numpy;
import os;
import sys;
from tables import *;
import wx;

for path in os.listdir("lib"):
  sys.path.append("lib/" + path);

for path in os.listdir("lib"):
  for subpath in os.listdir("lib/" + path):
    if (subpath[-3:] == ".py"):
      exec("from " + subpath[:-3] + " import *;");

matplotlib.interactive(True);
matplotlib.use("WXAgg");

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg;
from matplotlib.figure import Figure;

from GraphWindow import GraphWindow;
from GraphWindow import GraphDropTarget;
from HDFQS import *;

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

    self.tree = None;

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

################################## IMPORT MENU #################################
    # Structure
    menu_import = wx.Menu();

    self.importers = { };
    for importer in Importer.__subclasses__():
      menu_item = menu_import.AppendItem(wx.MenuItem(menu_import, wx.ID_ANY, importer.name + "\tCtrl+I"));
      self.importers[menu_item.GetId()] = importer;
      self.Bind(wx.EVT_MENU, self.onImport, menu_item);

    menubar.Append(menu_import, "&Import");

################################ FINISH MENUBAR ################################
    self.SetMenuBar(menubar);

################################################################################
################################# CREATE WINDOW ################################
################################################################################
  def create_window(self):
    self.tree = wx.TreeCtrl(self.window, wx.ID_ANY);
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
    self.current_file = temp["options"]["current_file"];
    self.load_file(self.current_file);
    self.graphs.set_options(temp["options"]);
    self.graphs.set_graph_config(temp["graph_config"]);
    self.graphs.load_data();
    self.current_config = path;

################################################################################
################################## SAVE CONFIG #################################
################################################################################
  def save_config(self, path=None):
    if (path == None):
      path = self.current_config;

    try:
      fd = open(path, "w");
      fd.write("graph_config = " + repr(self.graphs.get_graph_config()) + "\n");
      fd.write("options = " + repr(self.graphs.get_options()) + "\n");
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

    if (self.tree == None):
      self.create_window();
      self.graphs.set_current_file(self.current_file);
    else:
      self.tree.DeleteAllItems();

    self.hdfqs = HDFQS(path);
    self.populate_tree();

################################################################################
################################# POPULATE TREE ################################
################################################################################
  def populate_tree(self):
    self.tree.AddRoot("/");
    root = self.tree.GetRootItem();
    self.tree.SetItemHasChildren(root);
    groups = { };
    for path in self.hdfqs.manifest.keys():
      [ x, group_name, table_name ] = path.split("/");
      if (not groups.has_key(group_name)):
        groups[group_name] = self.tree.AppendItem(root, group_name);
      self.tree.AppendItem(groups[group_name], table_name);
    self.tree.Expand(root);

################################################################################
################################# EVENT HANDLERS ###############################
################################################################################

#################################### FILE NEW ##################################
  def onFileNew(self, e):
    dialog = wx.FileDialog(None, "New HDFQS file group...", ".", style=wx.FD_SAVE);
    if (dialog.ShowModal() == wx.ID_OK):
      path = dialog.GetPath();
      if (os.path.exists(path)):
	dialog = wx.MessageDialog(None, "File \"" + path + "\" exists - overwrite?", "Confirm", wx.YES_NO);
	if (dialog.ShowModal() != wx.ID_YES):
	  return;
      else:
	os.mkdir(path);
      HDFQS.initialize_file(path + "/index.h5");
      self.load_file(path);
      self.statusbar.SetStatusText("Created new file \"" + path + "\"");
    self.onFileSaveAs(e);

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

#################################### IMPORT ####################################
  def onImport(self, e):
    dialog = wx.FileDialog(None, "Import...", ".", style=wx.FD_OPEN);
    if (dialog.ShowModal() == wx.ID_OK):
      path = dialog.GetPath();
      if (os.path.exists(path)):
	importer = self.importers[e.GetId()];
	i = importer(self.current_file);
	i.import_data(path);
	self.load_file(self.current_file);

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
