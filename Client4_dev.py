import sounddevice as sd
import numpy as np
import socket
import time
import queue
import pyaudio
import sys
import threading
# from scipy.signal import firwin, filtfilt
from scipy.fft import dct, idct
import matplotlib.pyplot as plt

# class denoiser:
#     def __init__(self, fs) -> None:
        
#         self.bandpass = firwin(51, [100, 7900], pass_zero=False, fs=fs)
#         self.fs = fs

#     def denoise(self, data):
#         return filtfilt(self.bandpass, [1], data.reshape((len(data),)), padlen=len(self.bandpass)-1)




class Client:
    def __init__(self, target_ip, target_port, codeName, fs=8000, chunk_size=0.05, bits=16, chunk=1024, mute=False) -> None:
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.fs = fs  # Adjust as needed
        self.mute = mute
        self.chunk_size = chunk_size  # Adjust as needed
        self.bits = bits
        if bits == 8:
            format = pyaudio.paInt8
            self.type = np.int8
        elif bits == 16:
            format = pyaudio.paInt16
            self.type = np.int16
        self.first_packet = True
        self.counter = 0
        self.bufsize = int(bits//8 * fs * chunk_size)
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=format,
                    channels=1,
                    rate=fs,
                    output=True,
                    frames_per_buffer=chunk)
        # Set the target IP and port
        self.target_ip = target_ip
        self.target_port = target_port
        try:
            hello = f'HELLO,{codeName}'.encode('utf-8')
            self.s.sendto(hello, (target_ip, target_port))
            response, _ = self.s.recvfrom(1024)
            response = response.decode('utf-8')
            if response.startswith("SERVER:"):
                response = response.split(':')[1:]
                self.target_addr = (response[0], int(response[1]))
                print('Call Established Successfully')
            else :
                raise Exception("Bad Server response.")
        except Exception as e:
            print(f'Error in connection!, {e}')
            return
        self.connected = True
        self.noresponse = 0
        self.upStreamThread = threading.Thread(target=self.upStream)
        self.upStreamThread.start()
        self.downStream()

    def downStream(self):
        while self.connected:
            try:
                data, _ = self.s.recvfrom(self.bufsize+3)
                if data and not self.mute:
                    if self.first_packet == True:
                        self.first_packet == time.time()
                    if time.time() - self.first_packet > int.from_bytes(data[:3], "big") * self.chunk_size + self.chunk_size :
                        self.stream.write(data[3:])
                self.noresponse = 0
            except Exception as e:
                print(f'Error in downStream! {self.noresponse}, {e}')
                self.noresponse += 1
                if self.noresponse >= 10:
                    self.connected = False
            except KeyboardInterrupt:
                print('hanging up!')
                self.connected = False
        self.upStreamThread.join()
        self.hangUp()
        print("Hanged up!")

    def upStream(self):
        with sd.InputStream(samplerate=self.fs, channels=1, blocksize=self.bufsize//(self.bits//8), callback=self.callback):
            print("Microphone is UP!.")
            while self.connected:
                try:
                    # Read audio data from the microphone
                    data = ((q.get()))*(2 ** (self.bits-1) - 1)
                    # soundchunk = (dct(data.astype(float))/1024).astype(self.type)
                    
                    # print(np.max(np.abs(soundchunk)))
                    # # print(np.std(data))
                    # soundchunk = bytes((dct(data)/2.0).astype(self.type))
                    # soundchunk = (soundchunk/2.0)
                    # print(np.max(np.abs(soundchunk)), np.max(np.abs(soundchunk))/np.max(np.abs(data)))
                    # # soundchunk = soundchunk[:self.bufsize//(self.bits//8)//5].astype(self.type)

                    # data = bytes(soundchunk)
                    
                    data = bytes(data.astype(self.type))
                    self.s.sendto(self.counter.to_bytes(3, 'big') + data, self.target_addr)
                    self.counter += 1
                    # self.noresponse = 0
                except Exception as e:
                    print(f'Error in upStream! {self.noresponse}, {e}')
                    self.noresponse += 1
                    if self.noresponse >= 10:
                        self.connected = False
            return
    def hangUp(self):
        try:
            self.s.close()
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()
        except Exception:
            pass

    def callback(self, indata, frames, time, status):
        q.put(indata.copy())


if __name__ == "__main__":
    
    args = sys.argv[1:]
    q = queue.Queue()
    fs=20000
    chunk_size=0.03
    bits=16
    chunk=1024

    if len(args) > 0:
        if '-fs' in args:
            fs = int(args[args.index('-fs') + 1])
        if '-cs' in args:
            chunk_size = int(args[args.index('-cs') + 1])
        if '-b' in args:
            bits = int(args[args.index('-b') + 1])
        if '-ch' in args:
            chunk = int(args[args.index('-ch') + 1])
        call = Client(args[0], int(args[1]), args[2], fs, chunk_size, bits, chunk)
    else:
        args = ['', '', '', False]
        args[0] = input('IP: ')
    
        if args[0] == '':
            args[0] = 'localhost'
            args[1] = '3371'
            args[3] = False
            args[2] = '1'
        
        elif args[0] == 'm':
            args[0] = 'localhost'
            args[1] = '3371'
            args[3] = True
            args[2] = '1'
        else:
            args[1] = input('Port: ')
            args[2] = input('Room name: ')
        
        call = Client(args[0], int(args[1]), args[2], fs, chunk_size, bits, chunk, mute=args[3])
    
    print(input("Press any key to exit"))