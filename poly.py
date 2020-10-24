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

    

window = Tk()
window.geometry('1400x700')
window.resizable(False, False)


img_path = "C:\Study\Internship\App\dataset\ADE20K_2016_07_26\Images\img\ADE_train_00000001.jpg"


img = Image.open(img_path) 
img_height = img.size[1]
img_width = img.size[0] 

height = min(600, img_height)
width = min(1200, img_width)

canvas = Canvas(window, height = height, width = width, bg = 'white')
#canvas = XCanvas(window, height = height, width = width, bg = 'white')
canvas.place(x = 0, y = 50)


canvas_y_sb = Scrollbar(window, command = canvas.yview)
canvas_x_sb = Scrollbar(window, command = canvas.xview, orient = 'horizontal')
canvas_y_sb.place(x = 1210, y = 50, height = 600)
canvas_x_sb.place(x = 0, y = 660, width = 1200)
canvas.config(yscrollcommand = canvas_y_sb.set, xscrollcommand = canvas_x_sb.set)



canvas.configure(scrollregion=(0, 0, img_width, img_height  ))
imgtk = ImageTk.PhotoImage(img)
iid = canvas.create_image( img_width/2, img_height/2, image = imgtk )
img = cv2.imread(img_path[:50]+'labels'+img_path[56:-4]+'_seg.png')
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
labels = get_labels(img)

lb = Listbox(window)
lb.place(x = 1240, y = 300, height = 200)
lpsb = Scrollbar(window, command = lb.yview)
lpsb.place(x = 1349, y = 300, height = 200)
lb.config(yscrollcommand = lpsb.set) 
lp = np.array(labels)
for i in range(lp.shape[0]):
    lb.insert("end", rgb2hex(lp[i][0], lp[i][1], lp[i][2]))
    lb.itemconfig(i, {'bg':rgb2hex(lp[i][0], lp[i][1], lp[i][2])})
lb.select_set(0)


bn = Buttons(canvas, iid, img_height, img_width, window, lb)
new_polygon_bn = Button(window, text = 'Create mode', command = bn.create_mode)
new_polygon_bn.place(x = 1240, y = 10)

select_polygon_bn = Button(window, text = 'Edit mode', command = bn.edit_mode)
select_polygon_bn.place(x = 1240, y = 40)






save_bn = Button(window, text = 'Save', command = bn.save)
save_bn.place(x = 1240, y = 250)

undo_bn = Button(window, text = 'Undo', command = bn.undo)
undo_bn.place(x = 10, y = 20)

redo_bn = Button(window, text = 'Redo', command = bn.redo)
redo_bn.place(x = 50, y = 20)

del_all_bn = Button(window, text = 'Delete All', command = bn.deleteall)
del_all_bn.place(x = 90, y = 20)



draw(canvas, labels, img)
lb.bind("<Button-1>", bn.get_color) 

window.mainloop()