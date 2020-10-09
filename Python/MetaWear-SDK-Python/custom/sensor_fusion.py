# usage: python sensor_fusion.py [mac1] [mac2] ... [mac(n)]
from __future__ import print_function
from mbientlab.metawear import *
from mbientlab.metawear.cbindings import *
from time import sleep

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import platform
import sys
import copy
import threading
import csv

def connection():
    for s in states:
        print("Configuring device")
        libmetawear.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)
        sleep(1.5)

        signal= libmetawear.mbl_mw_settings_get_battery_state_data_signal(s.device.board)
        voltage = libmetawear.mbl_mw_datasignal_get_component(signal, Const.SETTINGS_BATTERY_VOLTAGE_INDEX)
        charge = libmetawear.mbl_mw_datasignal_get_component(signal, Const.SETTINGS_BATTERY_CHARGE_INDEX)

        libmetawear.mbl_mw_datasignal_subscribe(charge, None, s.callback_battery)
        libmetawear.mbl_mw_datasignal_read(voltage)
        libmetawear.mbl_mw_datasignal_read(charge)
        sleep(1.5)

        signal_corrected_gyro = libmetawear.mbl_mw_sensor_fusion_get_data_signal(s.device.board,SensorFusionData.CORRECTED_GYRO)
        libmetawear.mbl_mw_datasignal_subscribe(signal_corrected_gyro, None, s.callback)
        libmetawear.mbl_mw_sensor_fusion_enable_data(s.device.board, SensorFusionData.CORRECTED_GYRO)

        libmetawear.mbl_mw_sensor_fusion_set_acc_range(s.device.board,SensorFusionAccRange._16G)
        libmetawear.mbl_mw_sensor_fusion_set_gyro_range(s.device.board,SensorFusionGyroRange._1000DPS)
        libmetawear.mbl_mw_sensor_fusion_set_mode(s.device.board,SensorFusionMode.NDOF)
        libmetawear.mbl_mw_sensor_fusion_write_config(s.device.board)

        libmetawear.mbl_mw_sensor_fusion_start(s.device.board)
        input("")
        for s in states:
            libmetawear.mbl_mw_sensor_fusion_stop(s.device.board)
            libmetawear.mbl_mw_sensor_fusion_clear_enabled_mask(s.device.board)
            libmetawear.mbl_mw_datasignal_unsubscribe(signal_corrected_gyro)
            libmetawear.mbl_mw_debug_disconnect(s.device.board)
        write_on_csv(x,y,z)
def animate(i):  
    lines[0].set_data(t, x)
    lines[1].set_data(t, y)
    lines[2].set_data(t, z)
    if len(t) > xlim:
        ax.set_xlim(len(t) - xlim, len(t))
    else:
        ax.set_xlim(0, xlim)
    return lines
def write_on_csv(x,y,z):
        with open('measurements.csv', 'w', newline='') as file:
            writer = csv.writer(file, quoting=csv.QUOTE_NONNUMERIC, delimiter=';')
            writer.writerow(["counter","gyro-X","gyro-Y","gyro-Z"])
            for i in range(len(x)-1):
                r = []
                r.append(t[i])
                r.append(x[i])
                r.append(y[i])
                r.append(z[i])
                writer.writerow(r)
        return
class State:
    def __init__(self, device):
        self.device = device
        self.samples = 0
        self.callback = FnVoid_VoidP_DataP(self.data_handler)
        self.callback_battery=FnVoid_VoidP_DataP(self.battery_handler)
        self.gyro_data = []

    def data_handler(self, ctx, data):
        parsed_data=parse_value(data)
        print("%s -> %s" % (self.device.address, parsed_data))
        data_copy = copy.deepcopy(parsed_data)
        self.gyro_data.append(data_copy)
        self.samples+= 1
        t.append(self.samples)
        x.append(data_copy.x)
        y.append(data_copy.y)
        z.append(data_copy.z)

    def battery_handler(self, ctx, data):
        value = parse_value(data)
        # convert ms to ns
        print("Battery percentage: %s%%" % value)
class ZoomPan:
    def __init__(self):
        self.press = None
        self.cur_xlim = None
        self.cur_ylim = None
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.xpress = None
        self.ypress = None


    def zoom_factory(self, ax, base_scale = 2.):
        def zoom(event):
            cur_xlim = ax.get_xlim()
            cur_ylim = ax.get_ylim()

            xdata = event.xdata # get event x location
            ydata = event.ydata # get event y location

            if event.button == 'down':
                # deal with zoom in
                scale_factor = 1 / base_scale
            elif event.button == 'up':
                # deal with zoom out
                scale_factor = base_scale
            else:
                # deal with something that should never happen
                scale_factor = 1
                print(event.button)

            new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
            new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

            relx = (cur_xlim[1] - xdata)/(cur_xlim[1] - cur_xlim[0])
            rely = (cur_ylim[1] - ydata)/(cur_ylim[1] - cur_ylim[0])

            ax.set_xlim([xdata - new_width * (1-relx), xdata + new_width * (relx)])
            ax.set_ylim([ydata - new_height * (1-rely), ydata + new_height * (rely)])
            ax.figure.canvas.draw()

        fig = ax.get_figure() # get the figure of interest
        fig.canvas.mpl_connect('scroll_event', zoom)

        return zoom

    def pan_factory(self, ax):
        def onPress(event):
            if event.inaxes != ax: return
            self.cur_xlim = ax.get_xlim()
            self.cur_ylim = ax.get_ylim()
            self.press = self.x0, self.y0, event.xdata, event.ydata
            self.x0, self.y0, self.xpress, self.ypress = self.press

        def onRelease(event):
            self.press = None
            ax.figure.canvas.draw()

        def onMotion(event):
            if self.press is None: return
            if event.inaxes != ax: return
            dx = event.xdata - self.xpress
            dy = event.ydata - self.ypress
            self.cur_xlim -= dx
            self.cur_ylim -= dy
            ax.set_xlim(self.cur_xlim)
            ax.set_ylim(self.cur_ylim)

            ax.figure.canvas.draw()

        fig = ax.get_figure() # get the figure of interest

        # attach the call back
        fig.canvas.mpl_connect('button_press_event',onPress)
        fig.canvas.mpl_connect('button_release_event',onRelease)
        fig.canvas.mpl_connect('motion_notify_event',onMotion)

        #return the function
        return onMotion

states = []
x,y,z = [],[],[]
t = []
for i in range(len(sys.argv) - 1):
    d = MetaWear(sys.argv[i + 1])
    d.connect()
    print("Connected to " + d.address)
    states.append(State(d))

### Animated plot ###
th = threading.Thread(target=connection)
th.start()

fig = plt.figure()
xlim = 100
ylim = 1000
ax = plt.axes(xlim=(0, xlim), ylim=(-ylim, ylim))
lines = [plt.plot([], [])[0] for _ in range(3)]

anim = FuncAnimation(fig, animate, frames=200, interval=30, blit=False)

plt.show()

th.join()

print("Total Samples Received")
for s in states:
    print("%s -> %d" % (s.device.address, s.samples))

### Dynamic plot ###
fig, ax = plt.subplots()
plt.subplots_adjust(bottom = 0.25)

plt.axis([0, xlim, -ylim, ylim])
plt.plot(x, label = 'x-line', linewidth = 1)
plt.plot(y, label = 'y-line', linewidth = 1)
plt.plot(z, label = 'z-line', linewidth = 1)

plt.legend()
plt.title('Sensor fusion plot')
plt.ylabel('values')

zp = ZoomPan()
scale = 1.1
figZoom = zp.zoom_factory(ax, base_scale = scale)
figPan = zp.pan_factory(ax)

plt.show()
