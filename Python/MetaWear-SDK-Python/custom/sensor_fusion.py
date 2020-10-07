# usage: python stream_acc.py [mac1] [mac2] ... [mac(n)]
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
    plt.cla()
    plt.plot(x, label = 'x-line', linewidth = 1)
    plt.plot(y, label = 'y-line', linewidth = 1)
    plt.plot(z, label = 'z-line', linewidth = 1)
    plt.legend()
    plt.tight_layout()
def write_on_csv(x,y,z):
        with open('measurements.csv', 'a', newline='') as file:
            writer = csv.writer(file, quoting=csv.QUOTE_NONNUMERIC, delimiter=';')
            writer.writerow(["gyro-X","gyro-Y","gyro-Z"])
            for i in range(len(x)-1):
                r = []
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
        x.append(data_copy.x)
        y.append(data_copy.y)
        z.append(data_copy.z)

    def battery_handler(self, ctx, data):
        value = parse_value(data)
        # convert ms to ns
        print("Battery percentage: %s%%" % value)
states = []
x,y,z = [],[],[]
for i in range(len(sys.argv) - 1):
    d = MetaWear(sys.argv[i + 1])
    d.connect()
    print("Connected to " + d.address)
    states.append(State(d))

th = threading.Thread(target=connection)
th.start()
plt.ylim(-2000, 2000)
plt.plot(x, label = 'x-line', linewidth = 1)
plt.plot(y, label = 'y-line', linewidth = 1)
plt.plot(z, label = 'z-line', linewidth = 1)
plt.legend()

ani = FuncAnimation(plt.gcf(), animate, interval=1)

plt.title('Sensor fusion plot')
plt.ylabel('values')

plt.show()

th.join()

print("Total Samples Received")
for s in states:
    print("%s -> %d" % (s.device.address, s.samples))
#print("Gyro again just to be sure")
#for s in states:
#    for g in s.gyro_data:
#        print("%s -> %s" % (s.device.address, g))


## Plotting the data ##
'''
for s in states:
    plt.style.use('fivethirtyeight')

    x = []
    y = []
    z = []
    
    for g in s.gyro_data:      
        x.append(g.x)
        y.append(g.y)
        z.append(g.z)
        
    plt.ylim(-2000, 2000)
    plt.plot(x, label = 'x-line', linewidth = 1)
    plt.plot(y, label = 'y-line', linewidth = 1)
    plt.plot(z, label = 'z-line', linewidth = 1)
    plt.legend()

    plt.title('Sensor fusion plot')
    plt.ylabel('values')

    plt.show()
'''
