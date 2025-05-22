import numpy as np
import matplotlib.pyplot as plt
from itala import itala
import ctypes
import time
from cv2 import resize
import tifffile as tiff

class CamParams:
    def __init__(self, exposureMs=-1, timeoutMs = 10000):
        self.exposureMs=exposureMs#-1 leaves it unchanged #TODO integrate
        self.timeoutMs=timeoutMs
class Camera():
    def __init__(self,italaSys=None, logPath=''):
        #Optional logging of images in logPath
        self.logPath = logPath
        if italaSys is None:
            self.italaSys = itala.create_system()#TODO to global var
        else:
            self.italaSys = italaSys
            
    def setExposure(self,exposureMs): #TODO UNTESTED!
        exposure_time_node = self.nodemap.ExposureTime
        if(not itala.is_writable(exposure_time_node)):
            print("Unable to configure exposure time. Aborting")
            return
        original_exposure_time = exposure_time_node.value
        exposure_time_node.value = exposureMs
    # setExposure

    def connect(self, _serialNumber=0):#TODO unify with connection
        self.connected = False
        self.serialNumberConnect = int(_serialNumber)
        self.counter = 0

        print('connecting to cam')
        device_infos = self.italaSys.enumerate_devices(700)
        if len(device_infos)==0:
            print("No se encontraron interfaces de red")
            exit(1)
        print(f'Found devices')
        idConnect = -1
        if self.serialNumberConnect!=0:
            print(f"Specified serial number: {self.serialNumberConnect}")
            for i,dev in enumerate(device_infos):
                dev:itala.DeviceInfo #type hint (does not type the variable!)
                print(f'\t{i}\n\tdisplay_name {dev.display_name}\n\tserial {dev.serial_number}\n\tIP: {dev.ip_address}')
                if self.serialNumberConnect == int(dev.serial_number):
                    idConnect = i
                    break
            if idConnect == -1:
                print(f'serial number {self.serialNumberConnect} not found!')
                return
        else: #print serial numbers
            print("Unspecified serial number, these are the ones detected:")
            for i,dev in enumerate(device_infos): print(f'\t{i}\t{dev.serial_number}')
            if len(device_infos)>=1:
                idConnect=0
            else:
                print(f'No camera found!')
                return
        print(f'Connecting to {idConnect} \t {device_infos[idConnect].serial_number}')
        self.serialNumberConnect = device_infos[idConnect].serial_number
        device_info = device_infos[idConnect]
        
        self.connected = True
        try:
            self.device = self.italaSys.create_device(device_info)
            self.nodemap = self.device.node_map#to alter device properties, exposure, etc.
        except Exception as e:
            print(f'error while connecting to device\n\t{idConnect} \t {device_infos[idConnect].serial_number}\n{e}')
            self.connected = False
        
        self.printer('acquisition started')

    def printer(self,txt:str):
        print(f'[{self.serialNumberConnect}] {txt}')
        a=1

    def capture(self, params=CamParams())->np.ndarray:
        retries = 3
        while True:
            if retries <= 0:
                break
            retries-=1
            try:
                image = self.device.get_next_image(params.timeoutMs)
            except Exception as e:
                self.printer(f"No image available.\n Error\n\t{e}")
                continue
            if (image.is_incomplete):
                self.printer("Incomplete image received.")
                self.printer("Bytes filled: " + str(image.bytes_filled))
                self.printer("Timestamp: " + str(image.timestamp))
                time.sleep(1)
                continue
            
            height = image.height
            width = image.width
            fmt = image.pixel_format
            sizeImg = width * height

            channels = 1
            error = False

            # TODO add support for PfncFormat_Mono12p and PfncFormat_RGB12p!!
            if fmt == itala.PfncFormat_Mono8:
                channels = 1
            else:
                if fmt == itala.PfncFormat_RGB8:
                    channels = 3
                elif fmt == itala.PfncFormat_InvalidPixelFormat:
                    error = True
                else:
                    error = True
            if error:
                image.dispose()
                self.printer(f'format unsuported! only mono8 or rgb8!')
                break

            size = sizeImg * channels
            
            buffer = image.get_data()

            p = (ctypes.c_uint8 * size).from_address(int(buffer))
            nparray = np.ctypeslib.as_array(p)
            imageNp = nparray.reshape((height, width,channels)).squeeze().copy()
            if self.logPath!="":
                try:
                    minSizeW = 512
                    fileImage = f'{self.logPath}image{self.counter}.tiff'
                    f=min(minSizeW/float(imageNp.shape[0]),1.0)
                    imageWrite = resize(imageNp, None, fx=f, fy=f)
                    tiff.imwrite(fileImage, imageWrite)
                except Exception as e:
                    self.printer(f'Error while writing the image: {fileImage}\n{e}')
            self.counter+=1
            
            image.dispose()
            self.printer(f'capture OK {imageNp.shape}')
            self.device.stop_acquisition()

            return imageNp
        self.device.stop_acquisition()
        return None
    
    def disconnect(self):
        def tryDo(do):
            try: do()
            except Exception as e:
                self.printer(f'[Disconnect] {e}')
        tryDo(self.device.stop_acquisition)
        tryDo(self.device.dispose)

def plotImgs(imRgb,imTel): #TODO improve
    def resizeImg(im, minSizeW=128):
        f=min(minSizeW/float(im.shape[0]),1.0)
        return resize(im, None, fx=f, fy=f)
    listNums = plt.get_fignums()
    if len(listNums)==0:
        fig,ax=plt.subplots(2,1,figsize=(5,8))
    else:
        fig = plt.figure(listNums[0])
        ax = fig.get_axes()
    ax[0] = plt.subplot(2,1,1)
    ax[1] = plt.subplot(2,1,2)
    plt.tight_layout()
    ax[0].imshow(resizeImg(imRgb))
    ax[1].imshow(resizeImg(imTel))

    fig.canvas.draw()
    fig.canvas.flush_events()
    time.sleep(0.5)

def main():
    '''
    Script to connect, capture and save images for itala SDK.
    Main parameters: camera serial number for connection.
    Ensure correct parametrization of cameras prior to connection.
    TODO uniemplemented/tested device parametrization such as exposureMs
    TODO reduce capture latency
    TODO integrate capture with HW trigger
    TODO enable async capture calls (async/await)
    '''

    ID_CAM_RGB = 600742
    ID_CAM_TELE = 600590

    plt.ion() #enable interactive mode to plot while capturing // for plots while capturing without blocking
    
    camRGB = Camera(None,'./Captures/camRGB/')
    camRGB.connect(ID_CAM_RGB)
    
    camTele = Camera(camRGB.italaSys,'./Captures/camTele/')
    camTele.connect(ID_CAM_TELE)
    
    cams = [camRGB,camTele]
    all_connected = all(camera.connected for camera in cams)

    if all_connected: 
        print(f'Connected!')
    else:
        print(f'Not connected!')
        return
    
    counter = 0
    while True:
        t0=time.perf_counter()
        camRGB.device.start_acquisition()
        imRgb = camRGB.capture(CamParams(-1,10000))
        imTel = camTele.capture(CamParams(-1,50000))
        if (imRgb is None) or (imTel is None):
            print('Failed capture!')
            continue
        try:
            plotImgs(imRgb,imTel)
        except Exception as e:
            print(f"Error while plotting images\n\t{e}")        
            break
        counter+=1
        print(f'{counter}: {int((time.perf_counter()-t0)*1000)}ms')
    
    for cam in cams:
        cam.disconnect()

    plt.close()

    plt.ioff() #disable interactive mode // for plots while capturing without blocking

if __name__ == '__main__':
    main()