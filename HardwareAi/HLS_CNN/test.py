from pynq import Overlay, allocate
import sys, os, time, struct
import numpy as np

cfd = sys.path[0]

print('Loading overlay...')
overlay = Overlay(os.path.join(cfd, 'bitstream_60f', 'design_1_wrapper.bit'))
dma = overlay.axi_dma_0
print('Overlay loaded.')

# Begin tests

dir = os.path.join(cfd, 'test_values_60f')
in_buffer = allocate(shape=(421,), dtype=np.float32)
out_buffer = allocate(shape=(1,), dtype=np.int32)
in_player_id = 0
out_player_id = 0

for file in os.listdir(dir):
    if file.endswith(".in"):
        print('Testing file', file)
        f = open(os.path.join(dir, file), 'r')
        data = f.read().split(',')

        start_time = time.time()
        input_array = np.array(data).astype(np.float32)
        input_array = np.insert(input_array, 0, struct.unpack('f', struct.pack('i', in_player_id))[0], axis=0)
        in_buffer[:] = input_array
        in_player_id += 1
        dma.sendchannel.transfer(in_buffer)
        dma.sendchannel.wait()

        dma.recvchannel.transfer(out_buffer)
        dma.recvchannel.wait()
        out_player_id = out_buffer[0]

        dma.recvchannel.transfer(out_buffer)
        dma.recvchannel.wait()
        result = out_buffer[0]

        dma.recvchannel.transfer(out_buffer)
        dma.recvchannel.wait()
        certainty = struct.unpack('f', struct.pack('i', out_buffer[0]))[0]
        end_time = time.time()

        print('Player ID:', out_player_id)
        print('Output:', result)
        print('Certainty:', certainty)
        print('Time taken:', end_time - start_time)
