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

import matplotlib as mpl;
import os;
import seaborn as sns;
import sys;
from tables import *;
import wx;

for path in os.listdir("lib"):
  sys.path.append("lib/" + path);

for path in os.listdir("lib"):
  for subpath in os.listdir("lib/" + path):
    if (subpath[-3:] == ".py"):
      exec("from " + subpath[:-3] + " import *;");

mpl.interactive(True);

# Render negative sign properly
mpl.rcParams["font.sans-serif"].insert(0, "Liberation Sans");
mpl.rcParams["font.sans-serif"].insert(0, "Arial");
mpl.rcParams["font.family"] = "sans-serif";

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg;
from matplotlib.figure import Figure;

from GraphWindow import GraphWindow;
from HDFQS import *;
from PreferencesDialog import PreferencesDialog;

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
    menu_file_open = menu_file.AppendItem(wx.MenuItem(menu_file, wx.ID_OPEN, "&Open\tCtrl+O"));
    menu_file.AppendSeparator();
    menu_file_save = menu_file.AppendItem(wx.MenuItem(menu_file, wx.ID_SAVE, "&Save\tCtrl+S"));
    menu_file_save_as = menu_file.AppendItem(wx.MenuItem(menu_file, wx.ID_SAVEAS, "Save &As\tCtrl+A"));
    menu_file.AppendSeparator();
    menu_file_exit = menu_file.AppendItem(wx.MenuItem(menu_file, wx.ID_EXIT, "E&xit\tCtrl+Q"));
    menubar.Append(menu_file, "&File");

    menu_edit = wx.Menu();
    self.menu_edit_preferences = menu_edit.AppendItem(wx.MenuItem(menu_edit, wx.ID_PREFERENCES, "&Preferences"));
    self.menu_edit_preferences.Enable(False);
    menubar.Append(menu_edit, "&Edit");

    # Events
    self.Bind(wx.EVT_MENU, self.onFileNew, menu_file_new);
    self.Bind(wx.EVT_MENU, self.onFileOpen, menu_file_open);
    self.Bind(wx.EVT_MENU, self.onFileSave, menu_file_save);
    self.Bind(wx.EVT_MENU, self.onFileSaveAs, menu_file_save_as);
    self.Bind(wx.EVT_MENU, self.onFileExit, menu_file_exit);
    self.Bind(wx.EVT_MENU, self.onEditPreferences, self.menu_edit_preferences);

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

    self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.onTreeItemRightClick, id=self.tree.GetId());

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
    self.graphs.set_graph_markers(temp["markers"]);
    self.graphs.load_data();
    self.current_config = path;
    self.save_config(path);

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
      fd.write("markers = " + repr(self.graphs.markers) + "\n");
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
    self.graphs.set_hdfqs(self.hdfqs);
    self.populate_tree();

################################################################################
################################# POPULATE TREE ################################
################################################################################
  def populate_tree(self):
    self.tree.AddRoot("/");
    root = self.tree.GetRootItem();
    self.tree.SetItemHasChildren(root);
    locations = { };
    groups = { };
    for path in sorted(self.hdfqs.manifest.keys()):
      if (path == "FILES"):
        continue;
      try:
        [ x, location_name, group_name, table_name ] = path.split("/");
      except ValueError:
        continue;
      if (not locations.has_key(location_name)):
        locations[location_name] = self.tree.AppendItem(root, location_name);
        groups[location_name] = { };
      if (not groups[location_name].has_key(group_name)):
        groups[location_name][group_name] = self.tree.AppendItem(locations[location_name], group_name);
      self.tree.AppendItem(groups[location_name][group_name], table_name);
    self.tree.Expand(root);

################################################################################
################################# EVENT HANDLERS ###############################
################################################################################

#################################### FILE NEW ##################################
  def onFileNew(self, e):
    dialog = wx.DirDialog(None, "Select HDFQS file group...", ".", style=wx.DD_DIR_MUST_EXIST);
    if (dialog.ShowModal() == wx.ID_OK):
      path = dialog.GetPath();
      self.load_file(path);
      self.onFileSaveAs(e);
      self.menu_edit_preferences.Enable(True);

################################### FILE OPEN ##################################
  def onFileOpen(self, e):
    dialog = wx.FileDialog(None, "Open QSLife configuration file...", ".", style=wx.FD_OPEN, wildcard="*.py");
    if (dialog.ShowModal() == wx.ID_OK):
      path = dialog.GetPath();
      if (os.path.exists(path)):
	self.open_config(path);
	self.SetStatusText("Opened configuration file \"" + path + "\"");
        self.menu_edit_preferences.Enable(True);
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
      self.current_config = path;

################################### FILE EXIT ##################################
  def onFileExit(self, e):
    self.Close();

############################### EDIT PREFERENCES ###############################
  def onEditPreferences(self, e):
    dialog = PreferencesDialog(self.graphs.options, None, title="Preferences");
    if (dialog.ShowModal() == wx.ID_OK):
      timezone = int(dialog.timezone.GetValue());
      if ((timezone >= -12) and (timezone <= 14)):
        self.graphs.options["timezone"] = timezone;
        self.graphs.update();
      else:
	self.SetStatusText("Invalid timezone: %s" % dialog.timezone.GetValue());


#################################### IMPORT ####################################
  def onImport(self, e):
    dialog = wx.FileDialog(None, "Import...", ".", style=wx.FD_OPEN);
    if (dialog.ShowModal() == wx.ID_OK):
      path = dialog.GetPath();
      if (os.path.exists(path)):
	importer = self.importers[e.GetId()];
	i = importer();
	i.import_data(path);
	self.load_file(self.current_file);

############################# TREE ITEM RIGHT CLICK ############################
  def onTreeItemRightClick(self, e):
    root = self.tree.GetRootItem();
    item = e.GetItem();
    if (item == root):
      return;
    category = self.tree.GetItemParent(item);
    if (category == root):
      return;
    location = self.tree.GetItemParent(category);
    if (location == root):
      return;
    self.selected_source = "/" + self.tree.GetItemText(location) + "/" + self.tree.GetItemText(category) + "/" + self.tree.GetItemText(item);

    menu = wx.Menu();
    menu_create_graph = menu.AppendItem(wx.MenuItem(menu, wx.ID_ANY, "Create new graph"));
    self.Bind(wx.EVT_MENU, self.onCreateGraph, menu_create_graph);
    self.PopupMenu(menu);

  def onCreateGraph(self, e):
    config = dict(node=self.selected_source, new=True);
    self.graphs.show_graph_options(config);

if (__name__ == "__main__"):
  app = wx.App();
  QSLife(None);
  app.MainLoop();
