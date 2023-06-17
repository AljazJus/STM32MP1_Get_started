#!/usr/bin/python3

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GdkPixbuf
from gi.repository import Gst

import argparse
import signal
import os

import subprocess
import os.path
from os import path
from timeit import default_timer as timer

#init gstreamer
Gst.init(None)
Gst.init_check(None)
#init gtk
Gtk.init(None)
Gtk.init_check(None)


RESOURCES_DIRECTORY = os.path.abspath(os.path.dirname(__file__)) +"/"


class GstWidget(Gtk.Box):
    """
    Class that handles Gstreamer pipeline using gtkwaylandsink and appsink
    """
    def __init__(self, app ):#!
         super().__init__()
         # connect the gtkwidget with the realize callback
         self.connect('realize', self._on_realize)
         self.instant_fps = 0
         self.app = app


    def _on_realize(self, widget): #!
            """
            creation of the gstreamer pipeline when gstwidget is created
            """
            # gstreamer pipeline creation
            self.pipeline = Gst.Pipeline()

            # creation of the source v4l2src
            self.v4lsrc1 = Gst.ElementFactory.make("v4l2src", "source")
            video_device = "/dev/" + str(self.app.video_device)
            self.v4lsrc1.set_property("device", video_device)

            #creation of the v4l2src caps
            caps = str(self.app.camera_caps) + ", width=" + str(args.frame_width) +",height=" + str(args.frame_height) + ", framerate=" + str(args.framerate)+ "/1"
            print("Camera pipeline configuration : ",caps)
            camera1caps = Gst.Caps.from_string(caps)
            self.camerafilter1 = Gst.ElementFactory.make("capsfilter", "filter1")
            self.camerafilter1.set_property("caps", camera1caps)

            # creation of the videoconvert elements
            self.videoformatconverter1 = Gst.ElementFactory.make("videoconvert", "video_convert1")
            self.videoformatconverter2 = Gst.ElementFactory.make("videoconvert", "video_convert2")

            self.tee = Gst.ElementFactory.make("tee", "tee")

            # creation and configuration of the queue elements
            self.queue1 = Gst.ElementFactory.make("queue", "queue-1")
            self.queue2 = Gst.ElementFactory.make("queue", "queue-2")
            self.queue1.set_property("max-size-buffers", 1)
            self.queue1.set_property("leaky", 2)
            self.queue2.set_property("max-size-buffers", 1)
            self.queue2.set_property("leaky", 2)

            # creation and configuration of the appsink element
            self.appsink = Gst.ElementFactory.make("appsink", "appsink")
            self.appsink.set_property("emit-signals", True)
            self.appsink.set_property("sync", False)
            self.appsink.set_property("max-buffers", 1)
            self.appsink.set_property("drop", True)
            self.appsink.connect("new-sample", self.new_sample)

            # creation of the gtkwaylandsink element to handle the gestreamer video stream
            self.gtkwaylandsink = Gst.ElementFactory.make("gtkwaylandsink")
            self.pack_start(self.gtkwaylandsink.props.widget, True, True, 0)
            self.gtkwaylandsink.props.widget.show()

            # creation and configuration of the fpsdisplaysink element to measure display fps
            self.fps_disp_sink = Gst.ElementFactory.make("fpsdisplaysink", "fpsmeasure1")
            self.fps_disp_sink.set_property("signal-fps-measurements", True)
            self.fps_disp_sink.set_property("fps-update-interval", 2000)
            self.fps_disp_sink.set_property("text-overlay", False)
            self.fps_disp_sink.set_property("video-sink", self.gtkwaylandsink)
            self.fps_disp_sink.connect("fps-measurements",self.get_fps_display)

            # creation of the video rate and video scale elements
            self.video_rate = Gst.ElementFactory.make("videorate", "video-rate")
            self.video_scale = Gst.ElementFactory.make("videoscale", "video-scale")

            # Add all elements to the pipeline
            self.pipeline.add(self.v4lsrc1)
            self.pipeline.add(self.camerafilter1)
            self.pipeline.add(self.videoformatconverter1)
            self.pipeline.add(self.videoformatconverter2)
            self.pipeline.add(self.tee)
            self.pipeline.add(self.queue1)
            self.pipeline.add(self.queue2)
            self.pipeline.add(self.appsink)
            self.pipeline.add(self.fps_disp_sink)
            self.pipeline.add(self.video_rate)
            self.pipeline.add(self.video_scale)

            # linking elements together
            #                              -> queue 1 -> videoconvert -> fpsdisplaysink
            # v4l2src -> video rate -> tee
            #                              -> queue 2 -> videoconvert -> video scale -> appsink
            self.v4lsrc1.link(self.video_rate)
            self.video_rate.link(self.camerafilter1)
            self.camerafilter1.link(self.tee)
            self.queue1.link(self.videoformatconverter1)
            self.videoformatconverter1.link(self.fps_disp_sink)
            self.queue2.link(self.videoformatconverter2)
            self.videoformatconverter2.link(self.video_scale)
            self.video_scale.link(self.appsink)
            self.tee.link(self.queue1)
            self.tee.link(self.queue2)

            # set pipeline playing mode
            self.pipeline.set_state(Gst.State.PLAYING)
            # getting pipeline bus
            self.bus = self.pipeline.get_bus()
            self.bus.add_signal_watch()
            self.bus.connect('message::error', self.msg_error_cb)
            self.bus.connect('message::eos', self.msg_eos_cb)
            self.bus.connect('message::info', self.msg_info_cb)
            self.bus.connect('message::application', self.msg_application_cb)
            self.bus.connect('message::state-changed', self.msg_state_changed_cb)


    def msg_eos_cb(self, bus, message):
        print('eos message -> {}'.format(message))

    def msg_info_cb(self, bus, message):
        print('info message -> {}'.format(message))

    def msg_error_cb(self, bus, message):
        print('error message -> {}'.format(message.parse_error()))
        
    def msg_state_changed_cb(self, bus, message):
        oldstate,newstate,pending = message.parse_state_changed()
        if (oldstate == Gst.State.NULL) and (newstate == Gst.State.READY):
            Gst.debug_bin_to_dot_file(self.pipeline, Gst.DebugGraphDetails.ALL,"pipeline_py_NULL_READY")
            
    def msg_application_cb(self, bus, message):
        if message.get_structure().get_name() == 'inference-done':
            self.app.update_ui()

    def new_sample(self,*data):#! 
        """
        recover video frame from appsink
        and run inference
        """
        global image_arr
        sample = self.appsink.emit("pull-sample")
        
        struc = Gst.Structure.new_empty("inference-done")
        msg = Gst.Message.new_application(None, struc)
        self.bus.post(msg)
        return Gst.FlowReturn.OK
    
    def get_fps_display(self,fpsdisplaysink,fps,droprate,avgfps):#!
        """
        measure and recover display fps
        """
        self.instant_fps = fps
        return self.instant_fps
    
class MainWindow(Gtk.Window):
    """
    This class handles all the functions necessary
    to display video stream in GTK GUI or still
    pictures using OpenCVS
    """ 
    
    def __init__(self,args,app):
        """
        Setup instances of class and shared variables
        usefull for the application
        """
        Gtk.Window.__init__(self)
        self.app = app
        self.main_ui_creation(args)
       
    def set_ui_param(self):
        """
        Setup all the UI parameter depending
        on the screen size
        """
        self.ui_cairo_font_size_label = 35;
        self.ui_cairo_font_size = 20;
        self.ui_icon_exit_width = '50';
        self.ui_icon_exit_height = '50';
        self.ui_icon_st_width = '130';
        self.ui_icon_st_height = '160';
        if self.screen_height <= 272:
               # Display 480x272 */
               self.ui_cairo_font_size_label = 15;
               self.ui_cairo_font_size = 7;
               self.ui_icon_exit_width = '25';
               self.ui_icon_exit_height = '25';
               self.ui_icon_st_width = '42';
               self.ui_icon_st_height = '52';
        elif self.screen_height <= 480:
               #Display 800x480 */
               self.ui_cairo_font_size_label = 25;
               self.ui_cairo_font_size = 13;
               self.ui_icon_exit_width = '50';
               self.ui_icon_exit_height = '50';
               self.ui_icon_st_width = '65';
               self.ui_icon_st_height = '80';  

    def main_ui_creation(self,args):
        """
        Setup the Gtk UI of the main window
        """
        # remove the title bar
        self.set_decorated(False)

        self.first_drawing_call = True
        GdkDisplay = Gdk.Display.get_default()
        monitor = Gdk.Display.get_monitor(GdkDisplay, 0)
        workarea = Gdk.Monitor.get_workarea(monitor)

        GdkScreen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        css_path = RESOURCES_DIRECTORY + "py_widgets.css"
        self.set_name("main_window")
        provider.load_from_path(css_path)
        Gtk.StyleContext.add_provider_for_screen(GdkScreen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.maximize()
        self.screen_width = workarea.width
        self.screen_height = workarea.height

        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('destroy', Gtk.main_quit)
        self.set_ui_param()
        # setup info_box containing inference results and ST_logo which is a
        # "next inference" button in still picture mode
        if self.app.enable_camera_preview == True:
            # camera preview mode
            self.info_box = Gtk.VBox()
            self.info_box.set_name("gui_main_stbox")

            self.disp_fps = Gtk.Label()
            self.disp_fps.set_justify(Gtk.Justification.FILL)
            self.info_box.pack_start(self.disp_fps,True,False,2)
            
        # An overlay is used to keep a gtk drawing area on top of the video stream
        self.video_box = Gtk.HBox()
        self.video_box.set_name("gui_main_video")
        if self.app.enable_camera_preview == True:
            # camera preview => gst stream
            self.video_widget = self.app.gst_widget
            self.video_widget.set_app_paintable(True)
            self.video_box.pack_start(self.video_widget, True, True, 0)

        
        # setup the exit box which contains the exit button
        self.exit_box = Gtk.VBox()
        self.exit_box.set_name("gui_main_exit")
        self.exit_icon_path = RESOURCES_DIRECTORY + 'exit_' + self.ui_icon_exit_width + 'x' + self.ui_icon_exit_height + '.png'
        self.exit_icon = Gtk.Image.new_from_file(self.exit_icon_path)
        self.exit_icon_event = Gtk.EventBox()
        self.exit_icon_event.add(self.exit_icon)
        self.exit_box.pack_start(self.exit_icon_event,False,False,2)

        # setup main box which group the three previous boxes
        self.main_box =  Gtk.HBox()
        self.exit_box.set_name("gui_main")
        self.main_box.pack_start(self.info_box,False,False,0)
        self.main_box.pack_start(self.video_box,True,True,0)
        self.main_box.pack_start(self.exit_box,False,False,0)
        self.add(self.main_box)
        return True
    

class OverlayWindow(Gtk.Window):
    """
    This class handles all the functions necessary
    to display overlayed information on top of the 
    video stream and in side information boxes of
    the GUI
    """       
    def __init__(self,args,app):
        """
        Setup instances of class and shared variables
        usefull for the application
        """
        Gtk.Window.__init__(self)
        self.app = app
        self.overlay_ui_creation(args)
    
    def exit_icon_cb(self,eventbox, event):
        """
        Exit callback to close application
        """
        self.destroy()
        Gtk.main_quit()
        

    def set_ui_param(self):#!
        """
        Setup all the UI parameter depending
        on the screen size
        """
        self.ui_cairo_font_size_label = 35;
        self.ui_cairo_font_size = 20;
        self.ui_icon_exit_width = '50';
        self.ui_icon_exit_height = '50';
        self.ui_icon_st_width = '130';
        self.ui_icon_st_height = '160';
        if self.screen_height <= 272:
               # Display 480x272 */
               self.ui_cairo_font_size_label = 15;
               self.ui_cairo_font_size = 7;
               self.ui_icon_exit_width = '25';
               self.ui_icon_exit_height = '25';
               self.ui_icon_st_width = '42';
               self.ui_icon_st_height = '52';
        elif self.screen_height <= 480:
               #Display 800x480 */
               self.ui_cairo_font_size_label = 25;
               self.ui_cairo_font_size = 13;
               self.ui_icon_exit_width = '50';
               self.ui_icon_exit_height = '50';
               self.ui_icon_st_width = '65';
               self.ui_icon_st_height = '80';
    
    def overlay_ui_creation(self,args):#!
        """
        Setup the Gtk UI of the overlay window
        """
        # remove the title bar
        self.set_decorated(False)

        self.first_drawing_call = True
        GdkDisplay = Gdk.Display.get_default()
        monitor = Gdk.Display.get_monitor(GdkDisplay, 0)
        workarea = Gdk.Monitor.get_workarea(monitor)

        GdkScreen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        css_path = RESOURCES_DIRECTORY + "py_widgets.css"
        self.set_name("overlay_window")
        provider.load_from_path(css_path)
        Gtk.StyleContext.add_provider_for_screen(GdkScreen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.maximize()
        self.screen_width = workarea.width
        self.screen_height = workarea.height

        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('destroy', Gtk.main_quit)
        self.set_ui_param()

        # setup info_box containing inference results and ST_logo which is a
        # "next inference" button in still picture mode
        if self.app.enable_camera_preview == True:
            # camera preview mode
            self.info_box = Gtk.VBox()
            self.info_box.set_name("gui_overlay_stbox")
            self.disp_fps = Gtk.Label()
            self.disp_fps.set_justify(Gtk.Justification.FILL)
            self.info_box.pack_start(self.disp_fps,True,False,2)
            
        # setup video box containing a transparent drawing area
        # to draw over the video stream
        self.video_box = Gtk.HBox()
        self.video_box.set_name("gui_overlay_video")
        self.video_box.set_app_paintable(True)
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect("draw", self.drawing)
        self.drawing_area.set_name("overlay_draw")
        self.drawing_area.set_app_paintable(True)
        self.video_box.pack_start(self.drawing_area, True, True, 0)

        # setup the exit box which contains the exit button
        self.exit_box = Gtk.VBox()
        self.exit_box.set_name("gui_overlay_exit")
        self.exit_icon_path = RESOURCES_DIRECTORY + 'exit_' + self.ui_icon_exit_width + 'x' + self.ui_icon_exit_height + '.png'
        self.exit_icon = Gtk.Image.new_from_file(self.exit_icon_path)
        self.exit_icon_event = Gtk.EventBox()
        self.exit_icon_event.add(self.exit_icon)
        self.exit_icon_event.connect("button_press_event",self.exit_icon_cb)
        self.exit_box.pack_start(self.exit_icon_event,False,False,2)

        # setup main box which group the three previous boxes
        self.main_box =  Gtk.HBox()
        self.exit_box.set_name("gui_overlay")
        self.main_box.pack_start(self.info_box,False,False,0)
        self.main_box.pack_start(self.video_box,True,True,0)
        self.main_box.pack_start(self.exit_box,False,False,0)
        self.add(self.main_box)
        return True


    def drawing(self, widget, cr):
        """
        Drawing callback used to draw with cairo on
        the drawing area
        """
        if self.first_drawing_call :
            self.first_drawing_call = False
            self.drawing_width = widget.get_allocated_width()
            self.drawing_height = widget.get_allocated_height()
            cr.set_font_size(self.ui_cairo_font_size_label)
            self.boxes_printed = True
            if self.app.enable_camera_preview == False :
                self.app.still_picture_next = True
                if args.validation:
                    GLib.idle_add(self.app.process_picture)
                else:
                    self.app.process_picture()
            return False
        else :
            cr.set_font_size(self.ui_cairo_font_size_label)
            if self.app.enable_camera_preview == True:
                preview_ratio = float(args.frame_width)/float(args.frame_height)
                preview_height = self.drawing_height
                preview_width =  preview_ratio * preview_height
                if preview_width >= self.drawing_width:
                   preview_width = self.drawing_width
            else :
                preview_width = self.app.frame_width
                preview_height = self.app.frame_height
                if preview_width >= self.drawing_width:
                    preview_width = self.drawing_width
                   
                self.boxes_printed = True
                if args.validation:
                    self.app.still_picture_next = True   
        return True
    

    # Updating the labels and the inference infos displayed on the GUI interface - camera input
    def update_label_preview(self):
        """
        Updating the labels and the inference infos displayed on the GUI interface - camera input
        """
        display_fps = self.app.gst_widget.instant_fps
        str_display_fps = str("{0:.1f}".format(display_fps))
        self.disp_fps.set_markup("<span font=\'%d\' color='#FFFFFFFF'><b>%sfps\n</b></span>" % (self.ui_cairo_font_size,str_display_fps))

        if args.validation:
            # reload the timeout
            GLib.source_remove(self.app.valid_timeout_id)
            self.app.valid_timeout_id = GLib.timeout_add(10000,
                                                     self.app.valid_timeout_callback)

            self.app.valid_draw_count = self.app.valid_draw_count + 1
            # stop the application after 150 draws
            if self.app.valid_draw_count > 150:
                avg_prev_fps = sum(self.app.valid_preview_fps) / len(self.app.valid_preview_fps)
                avg_inf_time = sum(self.app.valid_inference_time) / len(self.app.valid_inference_time)
                avg_inf_fps = (1000/avg_inf_time)
                print("avg display fps= " + str(avg_prev_fps))
                print("avg inference fps= " + str(avg_inf_fps))
                print("avg inference time= " + str(avg_inf_time) + " ms")
                GLib.source_remove(self.app.valid_timeout_id)
                self.destroy()
                Gtk.main_quit()    
    

class Application:
    """
    Class that handles the whole application 
    """
    def __init__(self, args):
        #init variables uses :
        self.exit_app = False
        self.dcmipp_camera = False
        self.first_call = True
        #if args.image is empty -> camera preview mode else still picture
        if args.image == "":
            print("camera preview mode activate")
            self.enable_camera_preview = True
            #Test if a camera is connected
            check_camera_cmd = RESOURCES_DIRECTORY + "check_camera_preview.sh"
            check_camera = subprocess.run(check_camera_cmd)
            if check_camera.returncode==1:
                print("no camera connected")
                exit(1)
            self.video_device,self.camera_caps=self.setup_camera()
        else:
            print("NO CAMERA CONECTED") 
    
        self.valid_inference_time = []
        self.valid_preview_fps = []
        self.valid_draw_count = 0
        
        self.gst_widget = GstWidget(self) 
        #instantiate the main window
        self.main_window = MainWindow(args,self)
        
        #instantiate the overlay window
        self.overlay_window = OverlayWindow(args,self)
        self.main()
   
    def setup_camera(self): #!
        width = str(args.frame_width)
        height = str(args.frame_height)
        framerate = str(args.framerate)
        device = str(args.video_device)
        config_camera = RESOURCES_DIRECTORY + "setup_camera.sh " + width + " " + height + " " + framerate + " " + device
        x = subprocess.check_output(config_camera,shell=True)
        x = x.decode("utf-8")
        x = x.split("\n")
        for i in x :
            if "V4L_DEVICE" in i:     
                video_device = i.lstrip('V4L_DEVICE=')
            if "V4L2_CAPS" in i:
                camera_caps = i.lstrip('V4L2_CAPS=')
        return video_device, camera_caps
    
    def valid_timeout_callback(self):
        
        print("Timeout: camera preview and/or gtk is not behaving has expected\n");
        Gtk.main_quit()
        os._exit(1)

    def update_ui(self):
        self.overlay_window.update_label_preview()
        self.overlay_window.queue_draw()
     
    def main(self):
        self.main_window.connect("delete-event", Gtk.main_quit)
        self.main_window.show_all()
        self.overlay_window.connect("delete-event", Gtk.main_quit)
        self.overlay_window.show_all()
        # start a timeout timer in validation process to close application if
        # timeout occurs
        if args.validation:
            self.valid_timeout_id = GLib.timeout_add(35000,
                                                     self.valid_timeout_callback)
        return True

if __name__ == '__main__':
    # add signal to catch CRTL+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--image", default="", help="image directory with image to be classified")
    parser.add_argument("-v", "--video_device", default="", help="video device ex: video0")
    parser.add_argument("--frame_width", default=640, help="width of the camera frame (default is 320)")
    parser.add_argument("--frame_height", default=480, help="height of the camera frame (default is 240)")
    parser.add_argument("--framerate", default=60, help="framerate of the camera ")
    parser.add_argument("--validation", action='store_true', help="enable the validation mode")
    args = parser.parse_args()

    try:
        application = Application(args)

    except Exception as exc:
        print("Main Exception: ", exc )

    Gtk.main()
    print("gtk main finished")
    print("application exited properly")
    os._exit(0)
 
    