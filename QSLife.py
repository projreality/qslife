import wx;

class QSLife(wx.Frame):

  def __init__(self, *args, **kwargs):
    super(QSLife, self).__init__(*args, **kwargs);
    self.Show();

if (__name__ == "__main__"):
  app = wx.App();
  QSLife(None);
  app.MainLoop();
