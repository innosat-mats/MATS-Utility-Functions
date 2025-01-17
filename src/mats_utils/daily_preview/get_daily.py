from mats_utils.rawdata.read_data import read_MATS_data
import datetime as DT
import argparse
from datetime import date, timedelta
from mats_utils.plotting.plotCCD import all_channels_plot
import numpy as np
import sys
import multiprocessing

def generate_day_interval(snippet=False):
    # generates start time
    # three days ago
    # end time: two days ago

    today = date.today()
    start_day = today - timedelta(days=3)
    end_day = today - timedelta(days=2)

    start_time = DT.datetime(start_day.year,
                             start_day.month,
                             start_day.day,
                             0, 0, 0)

    if snippet:
        stop_time = start_time + timedelta(minutes=20)
    else:
        stop_time = DT.datetime(end_day.year,
                                end_day.month,
                                end_day.day,
                                0, 0, 0)
    return start_time, stop_time


def parallel_plotting(part):

    files_per_part = 250

    if int(len(CCDitems)) > files_per_part:
            
        if part == 0:
            start_point = 0
        else:
            start_point = part*files_per_part-1
        try:
            if (part+1)*files_per_part < int(len(CCDitems)):
                all_channels_plot(CCDitems[start_point:(part+1)*files_per_part-1], outdir=outdir+'part'+str(part)+'/', optimal_range=True, num_name=True)
            else:
                all_channels_plot(CCDitems[start_point:int(len(CCDitems))-1], outdir=outdir+'part'+str(part)+'/', optimal_range=True, num_name=True)
        except KeyboardInterrupt:
            sys.exit()
    else:
        try:
            all_channels_plot(CCDitems, outdir=outdir+'part0/', optimal_range=True, num_name=True)
        except KeyboardInterrupt:
            sys.exit()


parser = argparse.ArgumentParser(description='Plots measurements from previous'
                                 ' day specify data level and version of data')
parser.add_argument('--outdir', type=str,
                    help='output directory')
parser.add_argument('--level', type=str, default='1a',
                    help='choose between 1a or 1b')
parser.add_argument('--version', type=str, default='0.4',
                    help='specifies version of data')
parser.add_argument('--snippet', action="store_true", default=False,
                    help='If supplied; short interval for debugging')

args = parser.parse_args()

level = args.level
version = args.version
outdir = args.outdir
snippet = args.snippet

start_time, stop_time = generate_day_interval(snippet=snippet)

# get measurements
CCDitems = read_MATS_data(start_time, stop_time, level=level, version=version)
CCDitems = CCDitems.sort_values('EXPDate')

# generate figures
# note: issue when plotting several thousands of figures,
# plotting slows down. for now: split up by calling different output folders:

files_per_part = 250
sets = int(np.floor(len(CCDitems)/files_per_part))

parts = list(np.arange(0, sets))

pool = multiprocessing.Pool(8)
pool.map(parallel_plotting, parts)
