import os
import pytz
import platform

cur_path = os.path.dirname(os.path.realpath(__file__))
if platform.system() == 'Linux':
    driverPath = os.path.join(cur_path, '../chromedriver')
else:
    driverPath = os.path.join(cur_path, '../chromedriver/chromedriver.exe')
KST = pytz.timezone('Asia/Seoul')
if not os.path.isfile(driverPath):
    driverPath = os.path.join(cur_path, '../chromedriver')