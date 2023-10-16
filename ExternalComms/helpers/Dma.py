from pynq import Overlay, allocate
import pynq.lib.dma
import sys, os, re, struct
import numpy as np

class Dma:
    def __init__(self):
        self.overlay = None
        self.dma = None
    
    def initialize(self):
        cfd = f'{sys.path[0]}/../../../darren/MonkeysLaserTag/HardwareAi/HLS_CNN'
        print('Loading overlay...')
        self.overlay = Overlay(os.path.join(cfd, 'design_1_wrapper.bit'))
        self.dma = self.overlay.axi_dma_0
        print('Overlay loaded.')
    
    def send_to_ai(self, data):
        in_buffer = allocate(shape=(560,), dtype=np.float32)
        in_buffer[:] = np.array(data).astype(np.float32)
        self.dma.sendchannel.transfer(in_buffer)
        self.dma.sendchannel.wait()
    
    def send_to_ai_input_2d(self, data):
        in_buffer = allocate(shape=(560,), dtype=np.float32)
        asfloat = lambda i: float(i + 2**15) / 2**15 - 1.0
        inp = np.vectorize(asfloat)(data)
        in_buffer[:] = np.array(inp).astype(np.float32).flatten()
        self.dma.sendchannel.transfer(in_buffer)
        self.dma.sendchannel.wait()

    def recv_from_ai(self):
        out_buffer = allocate(shape=(1,), dtype=np.int32)

        self.dma.recvchannel.transfer(out_buffer)
        self.dma.recvchannel.wait()
        result = out_buffer[0]

        self.dma.recvchannel.transfer(out_buffer)
        self.dma.recvchannel.wait()
        print(out_buffer)
        certainty = struct.unpack('f', out_buffer[0])[0]
        print(certainty)

        return (int(result), float(certainty))
    
