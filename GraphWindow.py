import calendar;
from math import *;
import matplotlib;
from numpy import *;
from operator import itemgetter;
import os;
import re;
from tables import *;
import threading;
import time;
import wx;

from matplotlib.pyplot import *;

class GraphWindow(matplotlib.backends.backend_wxagg.FigureCanvasWxAgg):

################################################################################
################################## CONSTRUCTOR #################################
################################################################################
  def __init__(self, parent, id):
    self.figure = matplotlib.figure.Figure(None, None);
    super(GraphWindow, self).__init__(parent, id, self.figure);
    size = tuple(parent.GetClientSize());
    self.SetSize(size);
    self.figure.set_size_inches(float(size[0])/self.figure.get_dpi(), float(size[1])/self.figure.get_dpi());
    subplot = self.figure.add_subplot(1, 1, 1, visible=False);
    bb = subplot.get_window_extent().transformed(self.figure.dpi_scale_trans.inverted());
    self.figure_width = int(bb.width * self.figure.dpi);
    self.figure_x = bb.xmin * self.figure.dpi;

    self.Bind(wx.EVT_KEY_DOWN, self.onKeyDown);
    self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseWheel);

    self.options = { };
    self.options["clip"] = 1000;
    self.options["current_file"] = None;
    self.graph_config = [ ]; # List of data to graph
    self.markers = [ ];
    self.marker_lines = { };
    self.selected_marker = None;
    self.options["num_visible_graphs"] = 6;
    self.options["time_range"] = ( 0, 60000 ); # time range to display data
    self.options["timezone"] = 0;
    self.options["selected_graph"] = None;
    self.options["top_graph"] = 0;

    self.data = None;
    self.data_range = None;

    self.mpl_connect("button_press_event", self.onClick);
    self.mpl_connect("button_release_event", self.onRelease);
    self.mpl_connect("motion_notify_event", self.onMouseMove);

    self.lock_data = threading.Lock();

    self.EVTTYPE_UPDATE = wx.NewEventType();
    self.EVT_UPDATE = wx.PyEventBinder(self.EVTTYPE_UPDATE, 1);
    self.Bind(self.EVT_UPDATE, self.onUpdate);

################################################################################
################################### ON UPDATE ##################################
################################################################################
  def onUpdate(self, e):
    self.update();

################################################################################
################################### ON CLICK ###################################
################################################################################
  def onClick(self, e):
    closest_marker = self.find_nearby_marker(e.x - self.figure_x);
    if (e.guiEvent.LeftDClick()):
      if (closest_marker is None):
        self.create_marker(e);
      else:
        self.edit_marker(closest_marker);
    else:
      self.select_graph(e);
      self.selected_marker = closest_marker;

  def onRelease(self, e):
    self.selected_marker = None;

  def onMouseMove(self, e):
    if (self.selected_marker is not None):
      t = self.x_to_time(e.x);
      time_range = self.options["time_range"];
      #if (np.abs(self.selected_marker["time"] - t) > ((time_range[1] - time_range[0] ) / 50)):
      self.move_marker(self.selected_marker, self.x_to_time(e.x));

  def move_marker(self, marker, t):
    for l in self.marker_lines[marker["label"]]:
      l.remove();
      del l;
    self.marker_lines[marker["label"]] = [ ];
    marker["time"] = t;
    #e = wx.PyCommandEvent(self.EVTTYPE_UPDATE, wx.ID_ANY);
    #wx.PostEvent(self, e);
    for subplot in self.plots:
      self.draw_marker_line(subplot, marker);
    self.draw_marker_text(self.plots[-1], marker);
    self.draw();

  def find_nearby_marker(self, x):
    start = self.options["time_range"][0];
    stop = self.options["time_range"][1];
    closest_marker = None;
    closest_x = 5;
    for marker in self.markers:
      marker_x = np.round(float(marker["time"] - start) / (stop - start) * self.figure_width); # pixel X position of marker
      if (np.abs(marker_x - x) < closest_x):
        closest_x = np.abs(marker_x - x);
        closest_marker = marker;

    return closest_marker;

  def create_marker(self, e):
    marker_time = self.x_to_time(e.x);
    dialog = CreateMarkerDialog(marker_time + self.options["timezone"] * 3600000, None, title="New Marker");
    if (dialog.ShowModal() == wx.ID_OK):
      marker = { };
      marker["time"] = int(dialog.time.GetValue()) - self.options["timezone"] * 3600000;
      marker["label"] = dialog.label.GetValue();
      marker["color"] = "#FF0000";
      self.markers.append(marker);
      for subplot in self.plots:
        self.draw_marker_line(subplot, marker);
      self.draw_marker_text(self.plots[-1], marker);
      self.draw();

  def edit_marker(self, marker):
    dialog = CreateMarkerDialog(marker["time"] + self.options["timezone"] * 3600000, None, title="Edit Marker", marker=marker);
    if (dialog.ShowModal() == wx.ID_OK):
      for l in self.marker_lines[marker["label"]]:
        l.remove();
        del l;
      self.marker_lines[marker["label"]] = [ ];
      marker["time"] = int(dialog.time.GetValue()) - self.options["timezone"] * 3600000;
      marker["label"] = dialog.label.GetValue();
      marker["color"] = "#FF0000";
      self.markers.append(marker);
      for subplot in self.plots:
        self.draw_marker_line(subplot, marker);
      self.draw_marker_text(self.plots[-1], marker);
      self.draw();

  def x_to_time(self, x):
    pos = (x - self.figure_x) / self.figure_width;
    start = self.options["time_range"][0];
    stop = self.options["time_range"][1];
    return (stop - start) * pos + start;

  def select_graph(self, e):
    ( max_x, max_y ) = self.GetSize();
    x = e.x;
    y = max_y - e.y;
    top = 86; # Offset from top and bottom
    bottom = 75;
    sel = int(floor((y - top) / (max_y - top - bottom) * self.options["num_visible_graphs"] + self.options["top_graph"]));
    if ((sel >= self.options["top_graph"]) and ((sel - self.options["top_graph"]) < self.options["num_visible_graphs"])):
      self.options["selected_graph"] = sel;
    else:
      self.options["selected_graph"] = None;

################################################################################
################################ ON MOUSE WHEEL ################################
################################################################################
  def onMouseWheel(self, e):
    rot = e.GetWheelRotation();
    if ((self.options["selected_graph"] == None) or (rot == 0)):
      return;

    y_min = self.graph_config[self.options["selected_graph"]]["yscale"][0];
    y_max = self.graph_config[self.options["selected_graph"]]["yscale"][1];
    y_range = y_max - y_min;

    if (rot > 0):
      y_min = y_min + y_range / 5;
      y_max = y_max - y_range / 5;
    else:
      y_min = y_min - y_range / 4;
      y_max = y_max + y_range / 4;

    self.graph_config[self.options["selected_graph"]]["yscale"] = ( y_min, y_max );
    self.update();

################################################################################
############################### GET/SET OPTIONS ################################
################################################################################
  def get_options(self):
    return self.options;

  def set_options(self, options):
    self.options = options;
    return self;

################################################################################
############################### GET/SET TIME RANGE #############################
################################################################################
  def get_time_range(self):
    return self.options["time_range"];

  def set_time_range(self, time_range):
    self.options["time_range"] = time_range;
    return self;

################################################################################
############################## GET/SET GRAPH CONFIG ############################
################################################################################
  def get_graph_config(self):
    return self.graph_config;

  def set_graph_config(self, graph_config):
    self.graph_config = graph_config;
    with self.lock_data:
      self.data = [ ];
      for i in range(len(self.graph_config)):
	self.data.append(transpose(array([ [ ], [ ] ])));
    return self;

################################################################################
############################ GET/SET GRAPH MARKERS #############################
################################################################################
  def get_graph_markers(self):
    return self.markers;

  def set_graph_markers(self, markers):
    self.markers = markers;

################################################################################
################################## SET HDFQS ###################################
################################################################################
  def set_hdfqs(self, hdfqs):
    self.hdfqs = hdfqs;

################################################################################
################################# INSERT GRAPH ################################
################################################################################
  def add_graph(self, pos, config):
    if (pos == -1):
      self.graph_config.append(config);
    else:
      self.graph_config.insert(pos, config);

    with self.lock_data:
      self.data.append(transpose(array([ [ ], [ ] ])));

    self.load_data();

################################################################################
############################### GET/SET TOP GRAPH ##############################
################################################################################
  def get_top_graph(self):
    return self.options["top_graph"];

  def set_top_graph(self, top_graph):
    self.options["top_graph"] = top_graph;
    return self;

################################################################################
########################## GET/SET NUM VISIBLE GRAPHS ##########################
################################################################################
  def get_num_visible_graphs(self):
    return self.options["num_visible_graphs"];

  def set_num_visible_graphs(self, num_visible_graphs):
    self.options["num_visible_graphs"] = num_visible_graphs;
    return self;

################################################################################
############################## GET/SET CURRENT FILE ############################
################################################################################
  def get_current_file(self):
    return self.options["current_file"];

  def set_current_file(self, current_file):
    self.options["current_file"] = current_file;
    return self;

################################################################################
################################## GET/SET CLIP ################################
################################################################################
  def get_clip(self):
    return self.options["clip"];

  def set_clip(self, clip):
    self.options["clip"] = clip;
    return self;

################################################################################
################################ GET/SET TIMEZONE ##############################
################################################################################
  def get_timezone(self):
    return self.options["timezone"];

  def set_timezone(self, timezone):
    self.options["timezone"] = timezone;
    return self;

################################################################################
################################## LOAD DATA ###################################
################################################################################
  def load_data(self, force=False):
    load = False;
    gap = self.options["time_range"][1] - self.options["time_range"][0];
    if (force):
      load = True;
    elif ((self.data == None) or (self.data_range == None)):
      load = True;
    elif (len(self.graph_config) == 0):
      load = False;
    else:
      load = True;
    if (load):
      temp_data = [ ];
      for i in range(len(self.graph_config)):
        temp_data.append(transpose(array([ [ ], [ ] ])))
      for i in arange(len(self.graph_config)):
        entry = self.graph_config[i];
        x = self.hdfqs.load(entry["node"], self.options["time_range"][0], self.options["time_range"][1], self.figure_width, entry["time"], entry["value"]);
        if (x.shape != ( 0, )):
          mask_expr = self.graph_config[i]["valid"];
          if (mask_expr != ""):
            t = x[:,0];
            x = x[:,1];
            x = ma.masked_where(~eval(mask_expr), x);
            val = ma.concatenate(( t[:,newaxis], x[:,newaxis] ), axis=1);
          else:
            val = x;
        else:
          val = x;
        val = array(sorted(val.tolist(), key=itemgetter(0)));
        if (temp_data[i].shape == ( 0, 2 )):
          temp_data[i] = val;
        else:
          temp_data[i] = concatenate(( temp_data[i], val ));
	      
      self.data_range = (self.options["time_range"][0] - gap*1.5, self.options["time_range"][1] + gap*1.5);

      with self.lock_data:
	self.data = temp_data;

      e = wx.PyCommandEvent(self.EVTTYPE_UPDATE, wx.ID_ANY);
      wx.PostEvent(self, e);

################################################################################
##################################### UPDATE ###################################
################################################################################
  def update(self):
    if ((self.options["current_file"] == None) or (self.data == None)):
      return;

    # Condition for when time range is outside of range of available data, but still doing a GUI update
    if ((self.data_range == None) or (self.options["time_range"][0] < self.data_range[0]) or (self.options["time_range"][1] > self.data_range[1])):
      pass;

    self.figure.clear();

    ( ticks, labels ) = self.create_time_labels();

    start_date = time.strftime("%m/%d/%Y", time.gmtime(self.options["time_range"][0]/1000 + self.options["timezone"]*3600));
    stop_date = time.strftime("%m/%d/%Y", time.gmtime(self.options["time_range"][1]/1000 + self.options["timezone"]*3600));
    if (start_date == stop_date):
      date_label = "\n" + start_date;
    else:
      date_label = "\n" + start_date + " - " + stop_date;

    num = len(self.graph_config);
    with self.lock_data:
      data = list(self.data);
    self.plots = [ ];
    for i in arange(self.options["top_graph"], num):
      if ((i - self.options["top_graph"]) >= self.options["num_visible_graphs"]):
        break;
      subplot = self.figure.add_subplot(self.options["num_visible_graphs"], 1, i + 1 - self.options["top_graph"]);
      if (len(data[i]) == 0):
	val = array([]);
      else:
	t = data[i][:,0];
	val = data[i][:,1];
	disp = (t >= self.options["time_range"][0]) & (t <= self.options["time_range"][1]);
	t = t[disp];
	val = val[disp];

      if (len(val) != 0):
        valid = hstack(( True, diff(t) > 0 ));
        t = t[valid];
        val = val[valid];
	subplot.plot(t, val);

      subplot.get_axes().set_xlim(self.options["time_range"]);
      entry = self.graph_config[i];
      result = re.search("^/([A-Za-z0-9]+)/([A-Za-z0-9]+)/([A-Za-z0-9_]+?)(_([A-Za-z0-9]+))?$", entry["node"]).groups();
      if (result[4] is not None):
        subplot.set_ylabel(result[2] + "\n" + result[0] + "\n" + result[4], multialignment="center");
      else:
        subplot.set_ylabel(result[2] + "\n" + result[0] + "\n");
      ax = subplot.get_axes();
      ax.set_xticks(ticks);
      ax.set_xticklabels(labels);
      ax.set_ylim(entry["yscale"]);

      for marker in self.markers:
        self.draw_marker_line(subplot, marker);

      self.plots.append(subplot);

    for marker in self.markers:
      self.draw_marker_text(subplot, marker);
    try:
      subplot.set_xlabel(date_label);
    except UnboundLocalError:
      pass;
    self.draw();

  def draw_marker_line(self, subplot, marker):
    l = subplot.axvline(x=marker["time"], ymin=-1000000, ymax=1000000, c=marker["color"], zorder=0, clip_on=False);
    try:
      self.marker_lines[marker["label"]].append(l);
    except KeyError:
      self.marker_lines[marker["label"]] = [ l ];

  def draw_marker_text(self, subplot, marker):
    xlim = subplot.get_axes().get_xlim();
    x = marker["time"] + (xlim[1] - xlim[0]) / 100;
    ylim = subplot.get_axes().get_ylim();
    y = ylim[0] - (ylim[1] - ylim[0])/1.2;
    t = self.plots[-1].text(x, y, marker["label"], color=marker["color"], zorder=0, clip_on=False);
    self.marker_lines[marker["label"]].append(t);

################################################################################
#################################### KEY DOWN ##################################
################################################################################
  def onKeyDown(self, e):
    key_code = e.GetKeyCode();

    # Zoom in
    if (key_code == wx.WXK_NUMPAD_ADD):
      gap = self.options["time_range"][1] - self.options["time_range"][0];
      self.options["time_range"] = ( self.options["time_range"][0] + gap/4, self.options["time_range"][1] - gap/4 );
      self.load_data();
    # Zoom out
    elif (key_code == wx.WXK_NUMPAD_SUBTRACT):
      gap = self.options["time_range"][1] - self.options["time_range"][0];
      self.options["time_range"] = ( self.options["time_range"][0] - gap/2, self.options["time_range"][1] + gap/2 );
      self.load_data();
    # Move left
    elif ((key_code == wx.WXK_NUMPAD_LEFT) or (key_code == wx.WXK_NUMPAD4) or (key_code == wx.WXK_LEFT)):
      gap = self.options["time_range"][1] - self.options["time_range"][0];
      self.options["time_range"] = ( self.options["time_range"][0] - gap/2, self.options["time_range"][1] - gap/2 );
      self.load_data();
    # Move right
    elif ((key_code == wx.WXK_NUMPAD_RIGHT) or (key_code == wx.WXK_NUMPAD6) or (key_code == wx.WXK_RIGHT)):
      gap = self.options["time_range"][1] - self.options["time_range"][0];
      self.options["time_range"] = ( self.options["time_range"][0] + gap/2, self.options["time_range"][1] + gap/2 );
      self.load_data();
    elif ((key_code == wx.WXK_NUMPAD_UP) or (key_code == wx.WXK_NUMPAD8) or (key_code == wx.WXK_UP)):
      if (self.options["top_graph"] > 0):
	self.options["top_graph"] = self.options["top_graph"] - 1;
	self.update();
    elif ((key_code == wx.WXK_NUMPAD_DOWN) or (key_code == wx.WXK_NUMPAD2) or (key_code == wx.WXK_DOWN)):
      if (self.options["top_graph"] < len(self.graph_config) - 1):
	self.options["top_graph"] = self.options["top_graph"] + 1;
	self.update();
    elif (key_code == wx.WXK_NUMPAD_ENTER):
      dialog = GraphOptionsDialog(self, None, title="Graph Options - " + self.graph_config[self.options["selected_graph"]]["node"]);
      if (dialog.ShowModal() == wx.ID_OK):
	mask_expr = dialog.masking.GetValue();
	if (self.graph_config[self.options["selected_graph"]]["valid"] != mask_expr):
	  self.graph_config[self.options["selected_graph"]]["valid"] = mask_expr;
	  x = self.data[self.options["selected_graph"]];
	  x.mask = False;
	  if (mask_expr != ""):
	    t = x[:,0];
	    x = x[:,1];
	    x = ma.masked_where(~eval(mask_expr), x);
	    self.data[self.options["selected_graph"]] = ma.concatenate(( t[:,newaxis], x[:,newaxis] ), axis=1);
	ymin = float(dialog.ymin.GetValue());
	ymax = float(dialog.ymax.GetValue());
        new_value = dialog.value_field.GetStringSelection();
        if (self.graph_config[self.options["selected_graph"]]["value"] != new_value):
          self.graph_config[self.options["selected_graph"]]["value"] = new_value;
          self.load_data(True);
	self.graph_config[self.options["selected_graph"]]["yscale"] = ( ymin, ymax );
	self.update();
      dialog.Destroy();
    elif (key_code == wx.WXK_DELETE):
      if (self.options["selected_graph"] != None):
	dialog = wx.MessageDialog(None, "Are you sure you want to remove the graph?", "Confirm delete graph", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION);
	if (dialog.ShowModal() == wx.ID_YES):
	  with self.lock_data:
	    self.graph_config.pop(self.options["selected_graph"]);
	    self.data.pop(self.options["selected_graph"]);
	    self.options["selected_graph"] = None;
	  self.update();
    elif (key_code == wx.WXK_SPACE):
      dialog = GoToTimeDialog(self, None, title="Go to ...");
      result = dialog.ShowModal();

      if (result == wx.ID_OK):
	length = self.options["time_range"][1] - self.options["time_range"][0];
        try:
	  center_tuple = time.strptime(dialog.text_field.GetValue(), "%m/%d/%Y %H:%M:%S");
        except ValueError:
          try:
	    center_tuple = time.strptime(dialog.text_field.GetValue(), "%m/%d/%Y %H:%M");
          except ValueError:
            try:
	      center_tuple = time.strptime(dialog.text_field.GetValue(), "%m/%d/%Y");
            except ValueError:
              center_tuple = None;

        if (center_tuple is not None):
	  center = (calendar.timegm(center_tuple) - self.options["timezone"] * 3600) * 1000;
	  self.options["time_range"] = ( center - length/2, center + length/2 );
	  self.update();
	  self.load_data();

      dialog.Destroy();
    # Autoscale Y
    elif (key_code == 65):
      with self.lock_data:
	temp_data = list(self.data);
      if (self.options["selected_graph"] == None):
	return;
      elif (len(temp_data[self.options["selected_graph"]]) == 0):
	return;
      else:
	entry = self.graph_config[self.options["selected_graph"]];
	t = temp_data[self.options["selected_graph"]][:,0];
	disp = (t >= self.options["time_range"][0]) & (t <= self.options["time_range"][1]);
	data = temp_data[self.options["selected_graph"]][:,1][disp];
	if (data.shape != ( 0, )):
	  y_min = data.min();
	  y_max = data.max();
	  y_range = y_max - y_min;
	  y_min = floor(y_min - y_range * 0.15);
	  y_max = ceil(y_max + y_range * 0.15);
	  self.graph_config[self.options["selected_graph"]]["yscale"] = ( y_min, y_max );
	  self.update();
    else:
      e.Skip();

################################################################################
############################## CALCULATE STEP SIZE  ############################
################################################################################
  def calculate_step_size(self):
    gap = (self.options["time_range"][1] - self.options["time_range"][0]) / 1000;

    if (gap <= 5):
      step_size = 1;
    elif (gap <= 10):
      step_size = 2;
    elif (gap <= 30):
      step_size = 5;
    elif (gap < 60):
      step_size = 10;
    elif (gap <= 120):
      step_size = 15;
    elif (gap <= 300):
      step_size = 30;
    elif (gap <= 600):
      step_size = 60;
    elif (gap <= 1200):
      step_size = 150;
    elif (gap <= 1800):
      step_size = 300;
    elif (gap <= 3600):
      step_size = 450;
    elif (gap <= 8*3600):
      step_size = 3600;
    elif (gap <= 24*3600):
      step_size = 3*3600;
    else:
      step_size = 24*3600;

    step_size = step_size * 1000;

    return step_size;

################################################################################
############################### CREATE TIME LABELS  ############################
################################################################################
  def create_time_labels(self):
    step_size = self.calculate_step_size();
    start = floor(self.options["time_range"][0] / float(self.options["clip"]))*self.options["clip"];
    tick_start = ceil(start/float(step_size))*step_size;
    stop = ceil(self.options["time_range"][1] /float(self.options["clip"]))*self.options["clip"];
    tick_stop = floor(stop/float(step_size))*step_size;
    ticks = r_[tick_start:tick_stop+step_size:step_size];
    labels = [ "" ] * len(ticks);
    i = 0;
    for tick in ticks:
      labels[i] = time.strftime("%H:%M:%S", time.gmtime(tick/1000 + self.options["timezone"]*3600));
      i = i + 1;

    return ( ticks, labels );

################################################################################
############################### GRAPH DROP TARGET ##############################
################################################################################
class GraphDropTarget(wx.TextDropTarget):

  def __init__(self, object):
    super(GraphDropTarget, self).__init__();
    self.object = object;

  def OnDropText(self, x, y, data):
    config = { "node":data, "time":"time", "value":"value", "yscale":( 50, 150 ), "valid":"" };
    self.object.add_graph(-1, config);

################################################################################
################################## GRAPH DIALOG ################################
################################################################################
class GraphOptionsDialog(wx.Dialog):

  def __init__(self, parent, *args, **kwargs):
    super(GraphOptionsDialog, self).__init__(*args, **kwargs);

    self._parent = parent;

    self.create_gui();

    self.SetSize(( 390, 185 ));

  def create_gui(self):
    panel = wx.Panel(self);
    box = wx.StaticBox(panel, label="Graph Options");
    box_sizer = wx.StaticBoxSizer(box, wx.VERTICAL);
    sizer = wx.GridBagSizer(5, 5);

    sizer.Add(wx.StaticText(panel, label="Value field"), pos=( 0, 0 ), flag=wx.LEFT | wx.TOP, border=4);
    fields = self._parent.hdfqs.get_fields(self._parent.graph_config[self._parent.options["selected_graph"]]["node"]);
    fields.remove("time");
    fields.sort();
    self.value_field = wx.Choice(panel);
    self.value_field.SetItems(fields);
    self.value_field.SetStringSelection(self._parent.graph_config[self._parent.options["selected_graph"]]["value"]);
    sizer.Add(self.value_field, pos=( 0, 1 ), border=4);

    sizer.Add(wx.StaticText(panel, label="Valid condition"), pos=( 1, 0 ), border=4)

    self.masking = wx.TextCtrl(panel, size=( 250, -1 ));
    self.masking.SetValue(self._parent.graph_config[self._parent.options["selected_graph"]]["valid"]);
    self.masking.Bind(wx.EVT_KEY_DOWN, self.onKeyDown);
    sizer.Add(self.masking, pos=( 1, 1 ), span=( 1, 3) );

    sizer.Add(wx.StaticText(panel, label="Y min"), pos=( 2, 0 ), border=4);

    self.ymin = wx.TextCtrl(panel, size=( 75, -1 ));
    self.ymin.SetValue(str(self._parent.graph_config[self._parent.options["selected_graph"]]["yscale"][0]));
    self.ymin.Bind(wx.EVT_KEY_DOWN, self.onKeyDown);
    sizer.Add(self.ymin, pos=( 2, 1 ), span=( 1, 1 ));

    sizer.Add(wx.StaticText(panel, label="Y max"), pos=( 3, 0 ), flag=wx.LEFT | wx.TOP, border=4);

    self.ymax = wx.TextCtrl(panel, size=( 75, -1 ));
    self.ymax.SetValue(str(self._parent.graph_config[self._parent.options["selected_graph"]]["yscale"][1]));
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
    elif (key_code == wx.WXK_NUMPAD_ENTER):
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

################################################################################
############################## GO TO TIME DIALOG ###############################
################################################################################
class GoToTimeDialog(wx.Dialog):

  def __init__(self, parent, *args, **kwargs):
    super(GoToTimeDialog, self).__init__(*args, **kwargs);

    self.parent = parent;
    panel = wx.Panel(self);
    box = wx.StaticBox(panel, label="Go to");
    sizer = wx.StaticBoxSizer(box, wx.HORIZONTAL);
    self.text_field = wx.TextCtrl(panel, size=( 190, -1 ));
    center = ((self.parent.options["time_range"][0] + self.parent.options["time_range"][1]) / 2) / 1000 + self.parent.options["timezone"] * 3600;
    center_str = time.strftime("%m/%d/%Y %H:%M:%S", time.gmtime(center));
    self.text_field.SetValue(center_str);
    sizer.Add(self.text_field);
    panel.SetSizer(sizer);

    self.SetSize(( 200, 55 ));
    self.text_field.Bind(wx.EVT_KEY_DOWN, self.onKeyDown);

    self.text_field.SetFocus();

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

################################################################################
############################# CREATE MARKER DIALOG #############################
################################################################################
class CreateMarkerDialog(wx.Dialog):

  def __init__(self, marker_time, *args, **kwargs):
    if (kwargs.has_key("marker")):
      marker = kwargs.pop("marker");
    else:
      marker = { "time": marker_time, "label": "", "color": "#FF0000" };

    super(CreateMarkerDialog, self).__init__(*args, **kwargs);

    panel = wx.Panel(self);
    box = wx.StaticBox(panel, label="Marker");
    box_sizer = wx.StaticBoxSizer(box, wx.VERTICAL);
    sizer = wx.GridBagSizer(2, 2);

    sizer.Add(wx.StaticText(panel, label="Time"), pos=( 0, 0 ), flag=wx.LEFT | wx.TOP, border=4);
    self.time = wx.TextCtrl(panel, size=( 150, -1 ));
    self.time.SetValue(time.strftime("%m/%d/%Y %H:%M:%S", time.gmtime(np.floor(marker_time/1000))));
    sizer.Add(self.time, pos=( 0, 1 ));
    sizer.Add(wx.StaticText(panel, label="Label"), pos=( 1, 0 ), border=4);
    self.label = wx.TextCtrl(panel, size=( 150, -1));
    self.label.SetValue(marker["label"]);
    sizer.Add(self.label, pos=( 1, 1 ));

    self.time.Bind(wx.EVT_KEY_DOWN, self.on_key_down);
    self.label.Bind(wx.EVT_KEY_DOWN, self.on_key_down);

    box_sizer.Add(sizer);
    panel.SetSizer(box_sizer);
    self.SetSize(( 202, 78 ));

    self.label.SetFocus();

  def on_key_down(self, e):
    key_code = e.GetKeyCode();

    if (key_code == wx.WXK_ESCAPE):
      self.EndModal(wx.ID_CANCEL);
      self.Close();
    elif ((key_code == wx.WXK_RETURN) or (key_code == wx.WXK_NUMPAD_ENTER)):
      try:
        marker_time = time.strptime(self.time.GetValue(), "%m/%d/%Y %H:%M:%S");
      except ValueError:
        try:
          marker_time = time.strptime(self.time.GetValue(), "%m/%d/%Y %H:%M");
        except ValueError:
          try:
            marker_time = time.strptime(self.time.GetValue(), "%m/%d/%Y");
          except:
            marker_time = None;

      marker_time = calendar.timegm(marker_time) * 1000;
      if (marker_time is not None):
        self.time.SetValue(str(marker_time));
        self.EndModal(wx.ID_OK);
        self.Close();
    else:
      e.Skip();
