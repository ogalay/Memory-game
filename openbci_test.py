import argparse
from brainflow.board_shim import BoardShim, BrainFlowInputParams
import time

# Set params
parser = argparse.ArgumentParser()
parser.add_argument('--timeout', type=int, help='timeout for device discovery or connection', required=False,
                        default=0)
parser.add_argument('--serial-port', type=str,
                    help='serial port', required=False, default='COM4')
parser.add_argument('--board-id', type=int,
                    help='board id', required=False, default=0)

args = parser.parse_args()
params = BrainFlowInputParams()
params.serial_port = args.serial_port
openbci = BoardShim(args.board_id, params)

# Start record
openbci.prepare_session()
openbci.start_stream()

time.sleep(10)

# Get data
short_record = openbci.get_board_data()

# Stop record
openbci.stop_stream()
openbci.release_session()

print(short_record[[2, 3, 4, 6, 7, 8]])
ch_names = BoardShim.get_eeg_names(args.board_id)
print(ch_names)



