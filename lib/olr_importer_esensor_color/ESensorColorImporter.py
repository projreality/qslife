from tables import *

from Importer import *;

class ESensorColorRecord(IsDescription):
  time = Int64Col(pos=0);
  red = Int16Col(pos=1);
  green = Int16Col(pos=2);
  blue = Int16Col(pos=3);
  value = Int16Col(pos=4);

class ESensorColorImporter(Importer):

  name = "ESensor Color Light Sensor";

  def __init__(self, path):
    self.path = path;
    self.records = [  { "group":"/Environment",
		        "name":"light_esensor",
			"description":ESensorColorRecord,
			"units":{ "time": "ms since the epoch", "red": "DN", "green": "DN", "blue": "DN", "value": "DN" } } ];
    self.length = 24;
    self.fmt = ">QIIII";

  def preprocess(self):
    # Prune bad data
    self.data = self.data[self.data.max(axis=1)<2E12];

    conv_temp = -40 + 0.018*self.data[:,1];
    color_data = [ self.data[:,0], self.data[:,1], self.data[:,2], self.data[:,3], self.data[:,4] ];
    self.output = [ color_data ];
