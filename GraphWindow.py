import matplotlib;
import numpy;
from tables import *;
import wx;

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

    self.time_range = ( 0, 0 );
    self.graphs = [ ];

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
################################ SET CURRENT FILE ##############################
################################################################################
  def set_current_file(self, current_file):
    self.current_file = current_file;

################################################################################
################################# UPDATE GRAPHS ################################
################################################################################
  def update(self):
    self.figure.clear();

    num = len(self.graphs);
    fd = openFile(self.current_file, mode="r");
    for i in numpy.arange(num):
      entry = self.graphs[i];
      subplot = self.figure.add_subplot(num, 1, i + 1);
      data = numpy.array([ [ data[entry[1]], data[entry[2]] ] for data in fd.getNode(entry[0]).where("(time > " + str(self.time_range[0]) + ") & (time < " + str(self.time_range[1]) + ")") ]);
      subplot.plot(data[:,0], data[:,1]);
    fd.close();
    self.draw();

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
    else:
      e.Skip();
