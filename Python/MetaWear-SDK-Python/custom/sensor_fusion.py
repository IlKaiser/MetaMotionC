# usage: python stream_acc.py [mac1] [mac2] ... [mac(n)]
from __future__ import print_function
from mbientlab.metawear import *
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import platform
import sys
import copy

if sys.version_info[0] == 2:
    range = xrange

class State:
    def __init__(self, device):
        self.device = device
        self.samples = 0
        self.callback = FnVoid_VoidP_DataP(self.data_handler)
        self.gyro_data = []

    def data_handler(self, ctx, data):
        parsed_data=parse_value(data)
        print("%s -> %s" % (self.device.address, parsed_data))
        self.gyro_data.append(copy.deepcopy(parsed_data))
        self.samples+= 1

states = []
for i in range(len(sys.argv) - 1):
    d = MetaWear(sys.argv[i + 1])
    d.connect()
    print("Connected to " + d.address)
    states.append(State(d))

for s in states:
    print("Configuring device")
    libmetawear.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)
    sleep(1.5)

    signal_corrected_gyro = libmetawear.mbl_mw_sensor_fusion_get_data_signal(s.device.board,SensorFusionData.CORRECTED_GYRO)
    libmetawear.mbl_mw_datasignal_subscribe(signal_corrected_gyro, None, s.callback)
    libmetawear.mbl_mw_sensor_fusion_enable_data(s.device.board, SensorFusionData.CORRECTED_GYRO)

    libmetawear.mbl_mw_sensor_fusion_set_acc_range(s.device.board,SensorFusionAccRange._16G)
    libmetawear.mbl_mw_sensor_fusion_set_gyro_range(s.device.board,SensorFusionGyroRange._1000DPS)
    libmetawear.mbl_mw_sensor_fusion_set_mode(s.device.board,SensorFusionMode.NDOF)
    libmetawear.mbl_mw_sensor_fusion_write_config(s.device.board)

    libmetawear.mbl_mw_sensor_fusion_start(s.device.board)

sleep(5.0)

for s in states:
    libmetawear.mbl_mw_sensor_fusion_stop(s.device.board)
    libmetawear.mbl_mw_sensor_fusion_clear_enabled_mask(s.device.board)
    libmetawear.mbl_mw_datasignal_unsubscribe(signal_corrected_gyro)
    libmetawear.mbl_mw_debug_disconnect(s.device.board)

print("Total Samples Received")
for s in states:
    print("%s -> %d" % (s.device.address, s.samples))
#print("Gyro again just to be sure")
#for s in states:
#    for g in s.gyro_data:
#        print("%s -> %s" % (s.device.address, g))


## Plotting the data ##

for s in states:
    plt.style.use('fivethirtyeight')

    x = []
    y = []
    z = []
    
    for g in s.gyro_data:      
        x.append(g.x)
        y.append(g.y)
        z.append(g.z)
        
    plt.ylim(-500, 500)
    plt.plot(x, label = 'x-line', linewidth = 1)
    plt.plot(y, label = 'y-line', linewidth = 1)
    plt.plot(z, label = 'z-line', linewidth = 1)
    plt.legend()

    plt.title('Sensor fusion plot')
    plt.ylabel('values')

    plt.show()

