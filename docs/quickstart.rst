Quick Start
===========

Before starting this tutorial, download the `example HDFQS datastore <http://www.projreality.com/hdfqs/example.tgz>`_. Extract it into :file:`/tmp`::

  cd /tmp
  tar -xvf [YOUR DOWNLOADED LOCATION]/example.tgz

Start QSLife on the command line::

  python QSLife.py

This brings up the the QSLife window, with no configuration loaded.

.. image:: /images/initial_window.png
  :align: center
  :scale: 50%

From the menu, select :menuselection:`&File --> &New`.

First select the HDFQS data store extracted above in :file:`/tmp/example`.

Next, save the new configuration file in :file:`/tmp/example.py`.

The window now shows the loaded HDFQS data store. At the left is a tree, showing the HDFQS hierarchy. The locations can be expanded to show the categories, which can then be expanded to show the data tables.

.. image:: /images/tree.png
  :align: center

We will first set the timezone. To do this, go to :menuselection:`&Edit --> Preferences`. This brings up the Preferences dialog.

.. image:: /images/preferences.png
  :align: center

The example data was taken in the -0700 timezone. Enter :literal:`-7` for the timezone, and select :guilabel:`OK`.

To graph the temperature data, right click on the temperature_office data table and select :guilabel:`Create new graph`. This brings up the Graph Options dialog.

.. image:: /images/graph_options.png
  :align: center

The temperature data only has one value field (value). For certain kinds of data, a value field must be specified. For example, for accelerometer data, x, y, or z would generally need to be specified.

The valid condition is used to exclude invalid data. For example, movement artifacts can result in an invalid heart rate reading, so we can specify :literal:`x >= 40` to exclude heart rate values below 40 bpm. Alternately, some devices output a known value to indicate invalid or missing data. For example, if the invalid/missing "code" value was 512, we can specify :literal:`x != 512`. Note that the data value is always referred to as :literal:`x`.

The :guilabel:`Y min` and :guilabel:`Y max` fields set the Y axis scale.

Click :guilabel:`OK` to create the graph.

No data is shown yet, as the time range is not yet set. Click on the graph, then hit :kbd:`Spacebar` to bring up the dialog to specify the time. Enter :literal:`7/30/2014 00:00:00` (note - the time can be omitted, in which case :literal:`00:00:00` is assumed).

One last thing needs to be done - hit :kbd:`a` to autoscale the graph to the data. At this point, the data appears in the graph.

.. image:: /images/graph.png
  :align: center

The keyboard commands such as :kbd:`Spacebar` and :kbd:`a` above are used frequently in QSLife. In order for the commands to take effect, you must click on the graph area first. Subsequent commands don't require clicking on the graph area again, unless you have clicked outside of the graph area (e.g. on the tree to the left). Certain commands (such as the autoscale command used above) require that you click on the graph you want to change.

From the time labels on the X axis, we can see that only 60 seconds of data is shown in the graph. To zoom out, hit :kbd:`Numpad -`. Zoom out until 12:00 noon from 7/29 and 7/30 are both showing on the graph, then hit :kbd:`a` to autoscale the Y axis again.

.. image:: /images/graph2.png
  :align: center

Repeat the above steps to create and configure the humidity graph. Note that the displayed time range for all graphs is the same.

.. image:: /images/graph3.png
  :align: center

Markers can be added to the graph to mark significant times. For example, we can mark the time around 9pm on 7/29/2014 when the air conditioner was turned on.

First, zoom in using :kbd:`Numpad +`. Use :kbd:`Left arrow` and :kbd:`Right arrow` to move left and right in the graph. Autoscale to the data to make the change show more clearly. You can see that the humidity responded first, around 20:32, while the temperature responded a few minutes later.

.. image:: /images/ac_on_time.png
  :align: center

Double click on the point where the humidity starts to go down. This brings up the New Marker dialog.

.. image:: /images/new_marker.png
  :align: center

Check the box for :guilabel:`Line` to have a line show up at the marker time, and enter :literal:`AC on` into the :guilabel:`Label` field and hit :kbd:`Enter`. You can optionally also change the color of the marker. Note that you can cancel the marker by hitting :kbd:`Escape`.

.. image:: /images/marker.png
  :align: center

Double clicking on the marker line or either of the labels will bring up the Edit Marker dialog. You can also click and drag the marker to move it around.

Markers are useful to save a point in time for future reference. To illustrate this, hit the :kbd:`Right arrow` key multiple times to move away from the marker location. Then hit :kbd:`m` to bring up the marker list. You can see the "AC on" marker we just created. Double click on "AC on", and the graph is now centered on the time of the "AC on" marker.

Finally, select :menuselection:`&File --> &Save` to save the configuration changes.

Below is a keyboard command reference:

============== ========================
Key            Description
============== ========================
Numpad +       Zoom in
Numpad -       Zoom out
Left arrow     Move left
Right arrow    Move right
Up arrow       Shift graphs up
Down arrow     Shift graphs down
\*Numpad_enter Edit graph configuration
\*Delete       Delete graph
Spacebar       Go to time
\*a            Autoscale Y-axis to data
m              Marker list
============== ========================

\* These commands require first clicking on the target graph.
