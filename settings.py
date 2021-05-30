import os
import pytz
cur_path = os.path.dirname(os.path.realpath(__file__))
driverPath = os.path.join(cur_path, 'chromedriver.exe')
KST = pytz.timezone('Asia/Seoul')
if not os.path.isfile(driverPath):
    driverPath = os.path.join(cur_path, 'chromedriver')