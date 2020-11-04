from tkinter import *
import tkinter as tk
from tkinter.colorchooser import askcolor
from tkinter.filedialog import asksaveasfilename
from PIL import Image, ImageDraw, ImageTk
import os
from colormap import rgb2hex
import numpy as np
from collections import deque
import numpy as np
import math
import cv2 as cv2
from backgui import *
from colormap import rgb2hex

import tkinter as tk


sys.stderr = StdoutRedirector()
class XCanvas(tk.Canvas):
    def __init__(self, rootwin, height, width, bg, img_height, img_width, img):

        scrollbars = True
        scalewidget = True

        self.img_height = img_height
        self.img_width = img_width
        self.region = (0, 0, img_width, img_height)
        self.rootwin = rootwin
        self.img = img
        self.rootframe = tk.Frame(rootwin, width=width, height=height)
        self.rootframe.pack(expand=True, fill=tk.BOTH)
        tk.Canvas.__init__(self, self.rootframe, width=width, height=height, bg=bg, scrollregion=self.region)
        self.config(highlightthickness=0)

        #if scrollbars:
        #    self.scrollbars()

        self.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)
    
        # Scale Widget component
        self.scalewidget = tk.Scale(self.rootframe, from_=50, to=200, length=500,
                                    orient=tk.HORIZONTAL, font="Consolas 6", command=self.resize)
        self.scalewidget.set(100)
        self.scalewidget.place(x = 400, y = 20)
        #x1,y1,x2,y2 = self.bbox('all')
        #self.xview_scroll(-x2, "units")
        #self.yview_scroll(-y2, "units")
        self.xview_moveto(0)
        self.yview_moveto(0)
        #self.rootframe.focus_set()



    def resize(self, percent):
        x1,y1,x2,y2 = self.region
        canvas_breadth = max(x2-x1, y2-y1)
        _region = self.config('scrollregion')[4].split()
        region = tuple(float(x) for x in _region)
        x1,y1,x2,y2 = region
        breadth = max(x2-x1, y2-y1)
        if breadth == 0:
            return
        r = float(percent) / 100
        if r < 0.01 or r > 30:
            return
        s = r / (float(breadth) / canvas_breadth)
        self.scale('all', 0, 0, s, s)
        nregion = tuple(x*r for x in self.region)
        self.config(scrollregion=nregion)
    

    

window = Tk()
window.geometry('1500x800')
window.resizable(False, False)


img_path = "C:\Study\Internship\App\dataset\ADE20K_2016_07_26\Images\img\ADE_train_00000001.jpg"
olabels = np.load("dataset\ADE20K_2016_07_26\label.npy")

img = Image.open(img_path) 
img_height = img.size[1]
img_width = img.size[0] 

height = min(700, img_height)
width = min(1450, img_width)

canvas = Canvas(window, height = height, width = width, bg = 'white')
#canvas = XCanvas(window, height = height, width = width, bg = 'white', img_height = img_height, img_width = img_width, img = img)
canvas.place(x = 0, y = 50)


canvas_y_sb = Scrollbar(window, command = canvas.yview)
canvas_x_sb = Scrollbar(window, command = canvas.xview, orient = 'horizontal')
canvas_y_sb.place(x = width + 20, y = 50, height = height)
canvas_x_sb.place(x = 0, y = height + 70, width = width)
canvas.config(yscrollcommand = canvas_y_sb.set, xscrollcommand = canvas_x_sb.set)



canvas.configure(scrollregion=(0, 0, img_width, img_height  ))
imgtk = ImageTk.PhotoImage(img)
iid = canvas.create_image( img_width/2, img_height/2, image = imgtk )
canvas.iid = iid
#iid = -1
img = cv2.imread(img_path[:50]+'labels'+img_path[56:-4]+'_seg.png')
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
labels = get_labels(img)



bn = Buttons(canvas, iid, img_height, img_width, window, olabels)
new_polygon_bn = Button(window, text = 'Create mode', command = bn.create_mode)
new_polygon_bn.place(x = 188, y = 20)

select_polygon_bn = Button(window, text = 'Edit mode', command = bn.edit_mode)
select_polygon_bn.place(x = 268, y = 20)




save_bn = Button(window, text = 'Save', command = bn.save)
save_bn.place(x = 335, y = 20)


load_bn = Button(window, text = 'Load', command = bn.load)
load_bn.place(x = 375, y = 20)

export_bn = Button(window, text = 'Export', command = bn.export)
export_bn.place(x = 153, y = 20)

undo_bn = Button(window, text = 'Undo', command = bn.undo)
undo_bn.place(x = 10, y = 20)

redo_bn = Button(window, text = 'Redo', command = bn.redo)
redo_bn.place(x = 50, y = 20)

del_all_bn = Button(window, text = 'Delete All', command = bn.deleteall)
del_all_bn.place(x = 90, y = 20)

color_bn = Button(window, text = 'Select Color', command = bn.select_color_window)
color_bn.place(x = 417, y = 20)

"""def re():
    global canvas
    canvas.config(height = 600, width = 1300)

resize = Button(window, text = '.', command = re)
resize.place(x = 340, y = 70 + height)"""

draw(canvas, labels, img)

window.mainloop()