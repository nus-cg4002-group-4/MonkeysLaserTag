from pynq import Overlay, allocate
import pynq.lib.dma
import sys, os
import numpy as np

cfd = sys.path[0]

overlay = Overlay(os.path.join(cfd, 'design_1_wrapper.bit'))
dma = overlay.axi_dma_0

in_array = [1, 2, 3, 4]

in_buffer = allocate(shape=(4,), dtype=np.uint32)
out_buffer = allocate(shape=(4,), dtype=np.uint32)

in_buffer[:] = in_array

dma.sendchannel.transfer(in_buffer)
dma.recvchannel.transfer(out_buffer)
dma.sendchannel.wait()
dma.recvchannel.wait()
print(out_buffer)
