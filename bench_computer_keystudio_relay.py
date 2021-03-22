#!/usr/bin/python3

# coding: utf-8

''' FILE NAME
bench_computer_Keystudio_4.py

1. WHAT IT DOES
This is a GUI application that runs on any Raspberry Pi with a 40-pin header.
It requires a Keystudio 4 Channel Relay hat and a GPIO Screw Terminal Hat EP-0129.


2. REQUIRES
* Any Raspberry Pi with a 40-pin header.
* Keyestudio 4 Channel Relay HAT
* GPIO Screw Terminal Hat EP-0129
* DHT-22
* MCP-3008
* An optional GPIO breakout relay and GRPIO riser header
* Rapsberry Pi camera
* Raspberry Pi 7-inch touch screen
* Case

3. ORIGINAL WORK
Make A Raspberry Pi powered bench computer, Dr.Peter Dalmaris
Modification and additional code by Richard Inniss

'''

from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox

# Used with the camera functions
import picamera
import PIL
from PIL import ImageTk
from PIL import Image
import datetime  # used to create a unique file name for each image
import os

# Used with the environment functions
import pigpio
import DHT22
import Adafruit_DHT
from time import sleep, strftime
from gpiozero import MCP3008

PROGRAM_NAME = "AIoT Consulting Bench Computer"
IMAGE_FILE_LOCATION = "../photos"
VIDEO_FILE_LOCATION = "../videos"
DHT_SENSOR_PIN = 3
DHT_SENSOR_TYPE = 2302
DHT_FREQUENCY = 10000


class BenchComputer(Frame):

    def __init__(self, root):
        Frame.__init__(self, root)

        root.protocol("WM_DELETE_WINDOW",
                      self.on_closing)  # This will create a pop-up to confirm ending the program, and
        # if there is confirmation it will call the on_closing method
        # to tidy up before closing.
        # Bench control, Tab 1, variables
        self.lightOnImage = PhotoImage(file="icons/light-on.png")
        self.lightOffImage = PhotoImage(file="icons/light-off.png")
        self.fanOnImage = PhotoImage(file="icons/ac-on.png")
        self.fanOffImage = PhotoImage(file="icons/ac-off.png")
        self.ironOnImage = PhotoImage(file="icons/iron-on.png")
        self.ironOffImage = PhotoImage(file="icons/iron-off.png")
        self.gpioONImage = PhotoImage(file="icons/switch-on.png")
        self.gpioOFFImage = PhotoImage(file="icons/switch-off.png")
        self.hairdryerOnImage = PhotoImage(file="icons/hairdryer-on.png")
        self.hairdryerOffImage = PhotoImage(file="icons/hairdryer-off.png")

        # Camera, Tab 2 variables
        # Don't enable the camera if an actual camera is not connected to the RPi
        self.camera = picamera.PiCamera()
        self.last_photo = None  # declaring without defining.
        self.isVideoRecording = FALSE
        self.isTakingIntervalPhotos = FALSE
        self.intervalStillButtonPressed = FALSE
        self.intervalImageCounter = 0
        self.photoInterval = 5  # interval in seconds.
        self.directory_interval = None
        self.file_name_interval = None
        self.intervalCamera = PhotoImage(file="icons/multiple-shots.png")
        self.videoCamera = PhotoImage(file="icons/video-camera.png")
        self.add = PhotoImage(file="icons/add.png")
        self.remove = PhotoImage(file="icons/minus.png")
        self.stillCamera = PhotoImage(file="icons/photo-camera.png")

        # Environment, Tab 3 variables
        self.pi = pigpio.pi()
        # Don't setup the DHT sensor unless a sensor is actually connected
        self.sensor = DHT22.sensor(self.pi, DHT_SENSOR_PIN)
        self.clock = PhotoImage(file="icons/clock.png")
        self.humidity = PhotoImage(file="icons/humidity.png")
        self.thermometer = PhotoImage(file="icons/thermometer.png")
        self.light = PhotoImage(file="icons/lightbulb.png")

        # Setup relay GPIOS
        self.fan_gpio = 22  # On the relay board
        self.lights_gpio = 4  # On the relay board
        self.solder_iron_gpio = 6  # External relay
        self.hot_air_gpio = 26  # External relay
        self.ext_plug_one_gpio = 17  # External relay plug 1
        self.ext_plug_two_gpio = 27  # External relay plug 2
        self.pi.set_mode(self.hot_air_gpio, pigpio.OUTPUT)  # Make output
        self.pi.set_mode(self.solder_iron_gpio, pigpio.OUTPUT)  # Make output
        self.pi.set_mode(self.fan_gpio, pigpio.OUTPUT)  # Make output
        self.pi.set_mode(self.lights_gpio, pigpio.OUTPUT)  # Make output
        self.pi.set_mode(self.ext_plug_one_gpio, pigpio.OUTPUT)  # Make output
        self.pi.set_mode(self.ext_plug_two_gpio, pigpio.OUTPUT)  # Make output
        self.pi.write(self.hot_air_gpio, 0)  # Set to LOW
        self.pi.write(self.solder_iron_gpio, 0)  # Set to LOW
        self.pi.write(self.fan_gpio, 0)  # Set to LOW
        self.pi.write(self.lights_gpio, 0)  # Set to LOW
        self.pi.write(self.ext_plug_one_gpio, 0)  # Set to LOW
        self.pi.write(self.ext_plug_two_gpio, 0)  # Set to LOW

        self.pack(fill=BOTH, expand=True)
        self.root = root
        self.root.title(PROGRAM_NAME)
        self.root.iconphoto(False, PhotoImage(file='icons/aiot.png'))
        self.initUI()

    def initUI(self):
        self.root.update()  # I call update in order to draw the root window so that I can take its dimensions
        # in the next line.

        # Create the notebook with three tabs
        style = Style()
        mygreen = "#d2ffd2"
        myred = "#dd0202"

        style.theme_create("benchComputer",
                           parent="alt",
                           settings={
                               "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0]}},
                               "TNotebook.Tab": {
                                   "configure": {"padding": [10, 10], "background": mygreen},
                                   "map": {"background": [("selected", myred)],
                                           "expand": [("selected", [1, 1, 1, 0])]}}})

        style.theme_use("benchComputer")

        ##############################################################
        # You can also customise the theme for each frame, like this:
        # s = Style()
        # s.configure('Tab1.TFrame', background='cyan')
        # s.configure('Tab2.TFrame', background='red')
        # s.configure('Tab3.TFrame', background='magenta')

        # frame1 = Frame(width=400, height=300, style='Tab1.TFrame')
        # frame2 = Frame(width=400, height=300, style='Tab2.TFrame')
        # frame3 = Frame(width=400, height=300, style='Tab3.TFrame')
        ##############################################################

        # Create the notebook UI
        notebook = Notebook(self,
                            height=self.root.winfo_height(),
                            width=self.root.winfo_width() -180,
                            style="large.TNotebook")
        frame1 = Frame()
        frame2 = Frame()
        frame3 = Frame()

        notebook.add(frame1, text="Instruments")
        notebook.add(frame2, text="Camera")
        notebook.add(frame3, text="Environment")
        notebook.pack(pady=5, side=LEFT)

        # Create the log text area
        log_label = Label(self, text="Log")
        log_label.configure(background="white",
                            width=180,
                            justify=CENTER,
                            font=("Helvetica", 12))
        log_label.pack(side=TOP)
        self.log_textBox = Text(self,
                                height=self.root.winfo_height(),
                                width=180)
        self.log_textBox.pack(side=RIGHT)

        # Styles
        buttonStyle = Style()
        buttonStyle.configure("Normal.TButton",
                              background="#3495EB",
                              borderwidth=1, anchor = "center",
                              activeforeground="#30903C",
                              compound="BOTTOM")
        buttonStyle.configure("Selected.TButton",
                              background="#107B1D",
                              borderwidth=1, anchor = "center",
                              activeforeground="#30903C",
                              compound="BOTTOM")
        buttonStyle.configure("TextOnly.TButton",
                              borderwidth=1,
                              activeforeground="#30903C",
                              font=('Helvetica', '40'),
                              padding=(0, 0, 0, 0),
                              width=3,
                              height=3)

        # Styles for the camera and environment tabs
        intervalLabelStyle = Style()
        intervalLabelStyle.configure("IntervalLabel.TLabel",
                                     font=('Helvetica', '10'),
                                     padding=(0, 0, 0, 0),
                                     justify=LEFT)
        intervalLabelStyle.configure("Enrironment.TLabel",
                                     font=('Helvetica', '50'),
                                     padding=(0, 0, 0, 0),
                                     justify=LEFT)
        intervalLabelStyle.configure("EnrironmentTime.TLabel",
                                     font=('Helvetica', '30'),
                                     padding=(0, 10, 0, 0),
                                     justify=LEFT)

        cameraInfoLabelStyle = Style()
        cameraInfoLabelStyle.configure("cameraInfoLabel.TLabel",
                                       font=('Helvetica', '10'),
                                       padding=(0, 0, 0, 0),
                                       justify=LEFT)

        # Create the UI in the Instruments tab (frame1)
        Style().configure("TButton",
                          padding=(10, 10, 10, 10),
                          font='serif 10')  # Applies to all buttons

        frame1.columnconfigure(0, pad=3, weight=1)
        frame1.columnconfigure(1, pad=3, weight=1)
        frame1.columnconfigure(2, pad=3, weight=1)
        frame1.rowconfigure(0, pad=3, weight=1)
        frame1.rowconfigure(1, pad=3, weight=1)
        frame1.rowconfigure(2, pad=3, weight=1)

        self.lights1_button = Button(frame1,
                                     text="Lights 1",
                                     command=self.lightsToggle,
                                     image=self.lightOffImage,
                                     style="Normal.TButton")
        self.lights1_button.grid(row=0,
                                 column=0, sticky=W+E+N+S, padx=5, pady = 5)
        self.extractor_button = Button(frame1,
                                       text="Extractor",
                                       command=self.toggleFan,
                                       image=self.fanOffImage,
                                       style="Normal.TButton")
        self.extractor_button.grid(row=0,
                                   column=1, sticky=W+E+N+S, padx=5, pady = 5)
        self.solder_button = Button(frame1,
                                    text="solder",
                                    command=self.bigRelay1,
                                    image=self.ironOffImage,
                                    style="Normal.TButton")
        self.solder_button.grid(row=0,
                                column=2, sticky=W+E+N+S, padx=5, pady = 5)
        self.hotairgun_button = Button(frame1,
                                       text="Hot air gun",
                                       command=self.bigRelay2,
                                       image=self.hairdryerOffImage,
                                       style="Normal.TButton")
        self.hotairgun_button.grid(row=1,
                                   column=0, sticky=W+E+N+S, padx=5, pady = 5)
        self.plug_one_button = Button(frame1,
                                 text="GPIO 17",
                                 command   = self.extplugone,
                                 image=self.gpioOFFImage,
                                 style="Normal.TButton")
        self.plug_one_button.grid(row=1,
                             column=1, sticky=W+E+N+S, padx=5, pady = 5)
        self.plug_two_button = Button(frame1,
                                 text="GPIO 27",
                                 command   = self.extplugtwo,
                                 image=self.gpioOFFImage,
                                 style="Normal.TButton")
        self.plug_two_button.grid(row=1,
                             column=2, sticky=W+E+N+S, padx=5, pady = 5)

        # Create the UI in the Camera tab (frame2)
        self.cameraFrameLeft = Frame(frame2,
                                     height=self.root.winfo_height(),
                                     width=150,
                                     relief=SUNKEN)

        self.cameraFrameLeft.pack(pady=1,
                                  side=LEFT)

        self.cameraFrameRight = Frame(frame2,
                                      height=self.root.winfo_height(),
                                      width=450,
                                      relief=SUNKEN)  # This frame will contain the image preview
        self.cameraFrameRight.pack(pady=1,
                                   side=RIGHT)

        stillPhotoButton = Button(self.cameraFrameLeft,
                                  text="Still",
                                  command=self.take_still,
                                  image=self.stillCamera,
                                  style="Normal.TButton")

        stillPhotoButton.grid(row=0,
                              column=0,
                              rowspan=1)

        intervalPhotoButton = Button(self.cameraFrameLeft,
                                     text="Interval",
                                     command=self.startIntervalStill,
                                     image=self.intervalCamera,
                                     style="Normal.TButton")

        intervalPhotoButton.grid(row=1,
                                 column=0,
                                 rowspan=1)

        videoButton = Button(self.cameraFrameLeft,
                             text="Video",
                             command=self.toggleVideo,
                             image=self.videoCamera,
                             style="Normal.TButton")

        videoButton.grid(row=4,
                         column=0,
                         rowspan=2)

        self.intervalText = Label(self.cameraFrameLeft,
                                  text="Interval: {}s\n".format(self.photoInterval),
                                  style="IntervalLabel.TLabel")

        increaseInterval = Button(self.cameraFrameLeft,
                                  text="Increase",
                                  command=self.increase_photo_interval,
                                  image=self.add,
                                  style="Normal.TButton")

        decreaseInterval = Button(self.cameraFrameLeft,
                                  text="Decrease",
                                  command=self.decrease_photo_interval,
                                  image=self.remove,
                                  style="Normal.TButton")

        self.intervalText.grid(row=0,
                               column=1,
                               columnspan=2,
                               rowspan=1)

        increaseInterval.grid(row=1,
                              column=2)

        decreaseInterval.grid(row=1,
                              column=3)

        self.cameraStatus = Label(self.cameraFrameLeft,
                                  text="NOT RECORDING",
                                  style="cameraInfoLabel.TLabel")
                                  

        self.cameraStatus.grid(row=4,
                               column=2,
                               columnspan=2)

        # Create the UI in the Environment tab (frame3)
        temperatureLabel = Label(frame3, image=self.thermometer)
        humidityLabel = Label(frame3, image=self.humidity)
        timedateLabel = Label(frame3, image=self.clock)
        lightlevelLabel = Label(frame3, image=self.light)

        temperatureLabel.grid(row=0, column=0)
        humidityLabel.grid(row=1, column=0)
        lightlevelLabel.grid(row=2, column=0)
        timedateLabel.grid(row=3, column=0)

        self.temperatureLabel = Label(frame3, text="-", style="Enrironment.TLabel")
        self.temperatureLabel.grid(row=0, column=1)
        self.temperatureUnitLabel = Label(frame3, text="\u00b0C", style="Enrironment.TLabel")
        self.temperatureUnitLabel.grid(row=0, column=2)
        
        self.humidityLabel = Label(frame3, text="-", style="Enrironment.TLabel")
        self.humidityLabel.grid(row=1, column=1)
        self.humidityUnitLabel = Label(frame3, text="%", style="Enrironment.TLabel")
        self.humidityUnitLabel.grid(row=1, column=2)
        
        self.lightlevelLabel = Label(frame3,text="-", style="Enrironment.TLabel")
        self.lightlevelLabel.grid(row=2, column=1)
        self.lightlevelUnitLabel = Label(frame3, text="%", style="Enrironment.TLabel")
        self.lightlevelUnitLabel.grid(row=2, column=2)
        
        self.environmentTimeLabel = Label(frame3, text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                          style="EnrironmentTime.TLabel")
        self.environmentTimeLabel.grid(row=3, column=1, columnspan=5)

     

    # Environment - Tab 3 - methods
    def getDHTreadings(self):
        # Here is how to implement the sensor so that SUDO is not required
        # http://www.rototron.info/dht22-tutorial-for-raspberry-pi/
        # This works ok with Python 3

        self.sensor.trigger()
        sleep(.2)  # Necessary on faster Raspberry Pi's BUT I WILL NEED TO FIND A NON-BLOCKING WAY TO DELAY
        # SLEEP SHOULD NOT BE USED IN A GUI APPLICATION!!!

        # To convert Celsius to Farenheit, use this formula: (°C × 9/5) + 32 = °F
        temperature = self.sensor.temperature()
        humidity = self.sensor.humidity()
        ldr = MCP3008(channel=0, clock_pin=18, mosi_pin=24, miso_pin=23, select_pin=25) 
        light = round((100-(ldr.value*100)),2) # Dont forget to first install the gpiozero module and then...
                                               # ...add "from gpiozero import MCP3008" in the initial imports...

        self.temperatureLabel.config(text="{:3.2f}".format(temperature / 1.))
        self.humidityLabel.config(text="{:3.2f}".format(humidity / 1.))
        self.lightlevelLabel.config(text="{:3.2f}".format(light / 1.))
        self.environmentTimeLabel.config(text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))  # Prints out to the terminal
        print("{:3.2f}, {:3.2f}".format(temperature / 1., humidity / 1.))  # Prints out to the terminal

        self.root.after(DHT_FREQUENCY, self.getDHTreadings)

    # Camera - Tab 2 - methods
    def startIntervalStill(self):
        if self.intervalStillButtonPressed == FALSE:
            self.intervalStillButtonPressed = TRUE
            self.log_textBox.insert(0.0, "Pressed interval photo button. Interval button pressed is TRUE.\n")
            self.cameraStatus.config(text="Taking interval still images...")
            self.takeIntervalStill()
        else:
            self.intervalStillButtonPressed = FALSE
            self.log_textBox.insert(0.0, "Pressed interval photo button. Interval button pressed is FALSE.\n")
            self.cameraStatus.config(text="")

    def takeIntervalStill(self):
        # This method works like this:
        # Say the interval is set to 5 seconds
        # First, the method is called and the first photo is taken, and shown in the frame.
        # Second, this method is scheduled to be called again using the tkinter
        # root "after" method, at the set interval, unless the user has cancelled the
        # interval photo function by pressing the button again.
        if self.isTakingIntervalPhotos == FALSE and self.intervalStillButtonPressed == TRUE:
            self.directory_interval = '{}/Interval_{}'.format(IMAGE_FILE_LOCATION,
                                                              datetime.datetime.now().strftime("%B_%d_%y_%H_%M_%S"))
            # self.directory_interval       = '../photos/Interval_{}'.format(datetime.datetime.now().strftime("%B_%d_%y_%H_%M_%S"))
            if not os.path.exists(self.directory_interval):
                os.makedirs(self.directory_interval)
                self.file_name_interval = '{}/{}.jpg'.format(self.directory_interval, self.intervalImageCounter)
                self.intervalImageCounter += 1
                self.log_textBox.insert(0.0, "Taking an image every {} seconds, storing at location {}.\n".format(
                    self.photoInterval, self.directory_interval))
                self.isTakingIntervalPhotos = TRUE
                self.root.after(self.photoInterval, self.takeIntervalStill)
            else:
                self.log_textBox.insert(0.0,
                                        "Ended recording interval photos. Total {} taken, stored at location {}.\n".format(
                                            self.intervalImageCounter, self.interval))
                self.intervalImageCounter = 0

        if self.isTakingIntervalPhotos == TRUE and self.intervalStillButtonPressed == TRUE:
            self.intervalImageCounter += 1
            self.file_name_interval = '{}/{}.jpg'.format(self.directory_interval, self.intervalImageCounter)
            self.camera.rotation = 90
            self.camera.capture(self.file_name_interval)
            self.log_textBox.insert(0.0, "Captured interval image {}\n".format(self.file_name_interval))
            image = Image.open(self.file_name_interval)
            image = image.resize((350, 210), Image.ANTIALIAS)
            self.last_photo = ImageTk.PhotoImage(image)
            Label(self.cameraFrameRight, image=self.last_photo).grid(row=0, column=0)
            self.root.after(self.photoInterval * 1000, self.takeIntervalStill)

    def toggleVideo(self):
        if self.isVideoRecording == FALSE:
            self.isVideoRecording = TRUE
            file_name = '{}/{}.h264'.format(VIDEO_FILE_LOCATION, datetime.datetime.now().strftime("%B_%d_%y_%H_%M_%S"))
            self.log_textBox.insert(0.0, "Video is recording: {}\n".format(file_name))
            self.camera.rotation = 90
            self.camera.start_recording(file_name)
            self.cameraStatus.config(text="RECORDING...");
        else:
            self.isVideoRecording = FALSE
            self.log_textBox.insert(0.0, "Video is stopped\n")
            self.camera.stop_recording()
            self.cameraStatus.config(text="NOT RECORDING");

    def increase_photo_interval(self):
        self.photoInterval += 1
        self.log_textBox.insert(0.0, "Interval: {}s\n".format(self.photoInterval))
        self.intervalText.config(text="Interval: {}s\n".format(self.photoInterval), style="IntervalLabel.TLabel")

    def decrease_photo_interval(self):
        if self.photoInterval > 1:
            self.photoInterval -= 1
        self.log_textBox.insert(0.0, "Interval: {}s\n".format(self.photoInterval))
        self.intervalText.config(text="Interval: {}s\n".format(self.photoInterval), style="IntervalLabel.TLabel")

    def take_still(self):
        self.log_textBox.insert(0.0, "Capturing image...\n")
        file_name = '{}/{}.jpg'.format(IMAGE_FILE_LOCATION, datetime.datetime.now().strftime("%B_%d_%y_%H_%M_%S"))
        self.camera.rotation = 90
        self.camera.capture(file_name)
        self.log_textBox.insert(0.0, "Captured image {}\n".format(file_name))

        image = Image.open(file_name)
        image = image.resize((360, 216), Image.ANTIALIAS)
        self.last_photo = ImageTk.PhotoImage(image)
        Label(self.cameraFrameRight, image=self.last_photo).grid(row=0, column=0)

    # Bench control - Tab 1 - methods
    def bigRelay1(self):
        # The following works with the Keyestudio 4 Channel Relay HAT
        if self.pi.read(self.solder_iron_gpio) == 0:
            relay_value = "ON"
            self.solder_button.config(image=self.ironOnImage, style="Selected.TButton")
            self.pi.write(self.solder_iron_gpio, 1)
        else:
            relay_value = "OFF"
            self.solder_button.config(image=self.ironOffImage, style="Normal.TButton")
            self.pi.write(self.solder_iron_gpio, 0)
        self.log_textBox.insert(0.0, "Soldering iron is {}\n".format(relay_value))        

    def bigRelay2(self):
        # The following works with the Keyestudio 4 Channel Relay HAT
        if self.pi.read(self.hot_air_gpio) == 0:
            relay_value = "ON"
            self.hotairgun_button.config(image=self.hairdryerOnImage, style="Selected.TButton")
            self.pi.write(self.hot_air_gpio, 1)
        else:
            relay_value = "OFF"
            self.hotairgun_button.config(image=self.hairdryerOffImage, style="Normal.TButton")
            self.pi.write(self.hot_air_gpio, 0)
        self.log_textBox.insert(0.0, "Hot air gun is {}\n".format(relay_value))
        
    def toggleFan(self):
        print("toggleFan")
        # This works for the Keyestudio relay HAT
        if self.pi.read(self.fan_gpio) == 0:
            relay_value = "ON"
            self.extractor_button.config(image=self.fanOnImage, style="Selected.TButton")
            self.pi.write(self.fan_gpio, 1)
        else:
            relay_value = "OFF"
            self.extractor_button.configure(image=self.fanOffImage, style="Normal.TButton")
            self.pi.write(self.fan_gpio, 0)

        self.log_textBox.insert(0.0, "Fan is {}\n".format(relay_value))        

    def lightsToggle(self):
        print("lightsToggle")
        # This works for the Keyestudio relay HAT
        if self.pi.read(self.lights_gpio) == 0:
            relay_value = "ON"
            self.lights1_button.config(image=self.lightOnImage, style="Selected.TButton")
            self.pi.write(self.lights_gpio, 1)
        else:
            relay_value = "OFF"
            self.lights1_button.configure(image=self.lightOffImage, style="Normal.TButton")
            self.pi.write(self.lights_gpio, 0)

        self.log_textBox.insert(0.0, "Light is {}\n".format(relay_value))        

    def extplugone(self):
        # The following works with the Keyestudio 4 Channel Relay HAT
        if self.pi.read(self.ext_plug_one_gpio) == 0:
            relay_value = "ON"
            self.plug_one_button.config(image=self.gpioONImage, style="Selected.TButton")
            self.pi.write(self.ext_plug_one_gpio, 1)
        else:
            relay_value = "OFF"
            self.plug_one_button.config(image=self.gpioOFFImage, style="Normal.TButton")
            self.pi.write(self.ext_plug_one_gpio, 0)
        self.log_textBox.insert(0.0, "External Plug1 is {}\n".format(relay_value))

    def extplugtwo(self):
        # The following works with the Keyestudio 4 Channel Relay HAT
        if self.pi.read(self.ext_plug_two_gpio) == 0:
            relay_value = "ON"
            self.plug_two_button.config(image=self.gpioONImage, style="Selected.TButton")
            self.pi.write(self.ext_plug_two_gpio, 1)
        else:
            relay_value = "OFF"
            self.plug_two_button.config(image=self.gpioOFFImage, style="Normal.TButton")
            self.pi.write(self.ext_plug_two_gpio, 0)
        self.log_textBox.insert(0.0, "External Plug2 is {}\n".format(relay_value))

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):            
            self.root.destroy()

def main():
    root = Tk()
    root.attributes('-zoom', True)
    ex = BenchComputer(root)
    root.after(DHT_FREQUENCY, ex.getDHTreadings)  # This will trigger the first sensor reading
    root.mainloop()


if __name__ == '__main__':
    main()
