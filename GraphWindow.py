from math import *;
import matplotlib;
from numpy import *;
import re;
from tables import *;
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

    self.Bind(wx.EVT_KEY_DOWN, self.onKeyDown);

    self.time_range = ( 0, 0 ); # time range to display data
    self.graphs = [ ]; # List of data to graph
    self.clip = 1000;
    self.timezone = 0;
    self.num_visible_graphs = 6;
    self.top_graph = 0;
    self.current_file = None;

################################################################################
################################# SET TIME RANGE ###############################
################################################################################
  def set_time_range(self, time_range):
    self.time_range = time_range;

################################################################################
################################### SET GRAPHS #################################
################################################################################
  def set_graphs(self, graphs):
    self.graphs = graphs;

################################################################################
################################# INSERT GRAPH ################################
################################################################################
  def add_graph(self, pos, config):
    if (pos == -1):
      self.graphs.append(config);
    else:
      self.graphs.insert(pos, config);

################################################################################
################################ SET CURRENT FILE ##############################
################################################################################
  def set_current_file(self, current_file):
    self.current_file = current_file;

################################################################################
#################################### SET CLIP ##################################
################################################################################
  def set_clip(self, clip):
    self.clip = clip;

################################################################################
################################## SET TIMEZONE ################################
################################################################################
  def set_timezone(self, timezone):
    self.timezone = timezone;

################################################################################
################################# UPDATE GRAPHS ################################
################################################################################
  def update(self):
    if (self.current_file == None):
      return;

    self.figure.clear();

    ( ticks, labels ) = self.create_time_labels();

    num = len(self.graphs);
    fd = openFile(self.current_file, mode="r");
    for i in arange(self.top_graph, num):
      entry = self.graphs[i];
      subplot = self.figure.add_subplot(self.num_visible_graphs, 1, i + 1 - self.top_graph);
      data = array([ [ data[entry[1]], data[entry[2]] ] for data in fd.getNode(entry[0]).where("(time > " + str(self.time_range[0]) + ") & (time < " + str(self.time_range[1]) + ")") ]);
      if (len(data) != 0):
	subplot.plot(data[:,0], data[:,1]);
      else:
	subplot.get_axes().set_xlim(self.time_range);
      result = re.search("^/([A-Za-z0-9]+)/([A-Za-z0-9]+)_([A-Za-z0-9]+)$", entry[0]).groups();
      subplot.set_ylabel(result[1] + "\n" + result[2]);
      ax = subplot.get_axes();
      ax.set_xticks(ticks);
      ax.set_xticklabels(labels);
      ax.set_ylim(entry[3]);
    fd.close();

    self.draw();

################################################################################
#################################### KEY DOWN ##################################
################################################################################
  def onKeyDown(self, e):
    key_code = e.GetKeyCode();

    # Zoom in
    if (key_code == wx.WXK_NUMPAD_ADD):
      gap = self.time_range[1] - self.time_range[0];
      self.time_range = ( self.time_range[0] + gap/4, self.time_range[1] - gap/4 );
      self.update();
    # Zoom out
    elif (key_code == wx.WXK_NUMPAD_SUBTRACT):
      gap = self.time_range[1] - self.time_range[0];
      self.time_range = ( self.time_range[0] - gap/2, self.time_range[1] + gap/2 );
      self.update();
    # Move left
    elif ((key_code == wx.WXK_NUMPAD_LEFT) or (key_code == wx.WXK_NUMPAD4) or (key_code == wx.WXK_LEFT)):
      gap = self.time_range[1] - self.time_range[0];
      self.time_range = ( self.time_range[0] - gap/2, self.time_range[1] - gap/2 );
      self.update();
    # Move right
    elif ((key_code == wx.WXK_NUMPAD_RIGHT) or (key_code == wx.WXK_NUMPAD6) or (key_code == wx.WXK_RIGHT)):
      gap = self.time_range[1] - self.time_range[0];
      self.time_range = ( self.time_range[0] + gap/2, self.time_range[1] + gap/2 );
      self.update();
    elif ((key_code == wx.WXK_NUMPAD_UP) or (key_code == wx.WXK_NUMPAD8) or (key_code == wx.WXK_UP)):
      if (self.top_graph > 0):
	self.top_graph = self.top_graph - 1;
	self.update();
    elif ((key_code == wx.WXK_NUMPAD_DOWN) or (key_code == wx.WXK_NUMPAD2) or (key_code == wx.WXK_DOWN)):
      if (self.top_graph < len(self.graphs) - 1):
	self.top_graph = self.top_graph + 1;
	self.update();
    else:
      e.Skip();

################################################################################
############################## CALCULATE STEP SIZE  ############################
################################################################################
  def calculate_step_size(self):
    gap = (self.time_range[1] - self.time_range[0]) / 1000;

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
    start = floor(self.time_range[0] / float(self.clip))*self.clip;
    tick_start = ceil(start/float(step_size))*step_size;
    stop = ceil(self.time_range[1] /float(self.clip))*self.clip;
    tick_stop = floor(stop/float(step_size))*step_size;
    ticks = r_[tick_start:tick_stop+step_size:step_size];
    labels = [ "" ] * len(ticks);
    i = 0;
    for tick in ticks:
      labels[i] = time.strftime("%H:%M:%S", time.gmtime(tick/1000 + self.timezone*3600));
      i = i + 1;

    return ( ticks, labels );

################################################################################
############################### GRAPH DROP TARGET  #############################
################################################################################
class GraphDropTarget(wx.TextDropTarget):

  def __init__(self, object):
    super(GraphDropTarget, self).__init__();
    self.object = object;

  def OnDropText(self, x, y, data):
    config = [ data, "time", "value", ( 50, 150 ) ];
    self.object.add_graph(-1, config);
    self.object.update();
