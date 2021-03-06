from tkinter import *
import tkinter as tk
from tkinter.colorchooser import askcolor
from tkinter import colorchooser
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
from tkinter import messagebox
import tkinter as tk
import tkinter.font as tkfont


def run(linked = False, img_to_open = None, seg = None, root = None):
    if not linked:
        sys.stderr = StdoutRedirector()

    
    if(root == None):
        window = Tk()
    else:
        window = Toplevel(root)
    window.option_add('*Font', 'TkDefaultFont 9')
    window.geometry('1500x760')
    window.resizable(False, False)
    window.title('Polygonal Annotation tool')
    ##files = [('JPG File', '*.jpeg')]
    ##filename = askopenfilename(parent=self.window, initialdir = os.getcwd(),title = "Select file",defaultextension = json, filetypes = files)

    olabels = None

    img_height = 700
    img_width = 1250 

    height = img_height#min(700, img_height)
    width = img_width#min(1250, img_width)

    canvas = Canvas(window, height = height, width = width, bg = 'white')
    #canvas = XCanvas(window, height = height, width = width, bg = 'white', img_height = img_height, img_width = img_width, img = img)
    canvas.place(x = 210, y = 0)


    canvas_y_sb = Scrollbar(window, command = canvas.yview)
    canvas_x_sb = Scrollbar(window, command = canvas.xview, orient = 'horizontal')
    canvas_y_sb.place(x = width + 220, y = 0, height = height)
    canvas_x_sb.place(x = 210, y = height + 7, width = width)
    canvas.config(yscrollcommand = canvas_y_sb.set, xscrollcommand = canvas_x_sb.set)



    ##canvas.configure(scrollregion=(0, 0, img_width, img_height  ))
    imgtk = None
    iid = -1
    ##iid = canvas.create_image( img_width/2, img_height/2, image = imgtk )
    #canvas.iid = iid
    #iid = -1
    #img = cv2.imread(img_path[:50]+'labels'+img_path[56:-4]+'_seg.png')
    #img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    #labels = get_labels(img)



    bn = Buttons(canvas, iid, img_height, img_width, window, olabels)
    bn.canvas_y_sb = canvas_y_sb
    bn.canvas_x_sb = canvas_x_sb


    new_polygon_bn = Button(window, text = 'Create mode', command = bn.create_mode)
    new_polygon_bn.place(x = 30, y = 20)

    select_polygon_bn = Button(window, text = 'Edit mode', command = bn.edit_mode)
    select_polygon_bn.place(x = 115, y = 20)

    bn.lb = Listbox(window, highlightcolor = None)
    bn.lb.place(x = 30, y = 90, height = 180, width = 150)
    lbl =  Label(window, text = 'Choose Class')
    lbl.place(x = 28, y = 65)
    lpsb = Scrollbar(window, command = bn.lb.yview)
    lpsb.place(x = 180, y = 90, height = 180)
    bn.lb.config(yscrollcommand = lpsb.set) 

    lb_create_bn = Button(window, text = 'Create/Edit',command =  bn.create_new_color)
    lb_create_bn.place(x = 12, y = 275)

    lb_save_bn = Button(window, text = 'Save',command =  bn.save_new_list)
    lb_save_bn.place(x = 125, y = 275)

    lb_load_bn = Button(window, text = 'Load',command =  bn.load_new_list)
    lb_load_bn.place(x = 163, y = 275)

    lb_clear_bn = Button(window, text = "Clear", command = bn.clear_list)
    lb_clear_bn.place(x = 85, y = 275)

    ##save_bn = Button(window, text = 'Save', command = bn.save)
    ##save_bn.place(x = 335, y = 20)


    ##load_bn = Button(window, text = 'Load', command = bn.load)
    ##load_bn.place(x = 375, y = 20)

    ##export_bn = Button(window, text = 'Export', command = bn.export)
    ##export_bn.place(x = 153, y = 20)

    ##undo_bn = Button(window, text = 'Undo', command = bn.undo)
    ##undo_bn.place(x = 10, y = 20)

    ##redo_bn = Button(window, text = 'Redo', command = bn.redo)
    ##redo_bn.place(x = 50, y = 20)

    ##del_all_bn = Button(window, text = 'Delete All', command = bn.deleteall)
    ##del_all_bn.place(x = 90, y = 20)


    

    def exit():
        sys.exit()

    menubar = Menu(window)
    filemenu = Menu(menubar, tearoff = 0)
    menubar.add_cascade(label="File", menu=filemenu)
    filemenu.add_command(label="Open Project", command=bn.load)
    filemenu.add_command(label="Save Project", command=bn.save)
    filemenu.add_command(label="Export as PNG", command=bn.export)
    filemenu.add_command(label="Open background image", command=bn.open_img)
    filemenu.add_command(label="Open segmentation map", command=bn.auto_create)
    filemenu.add_command(label="Exit", command=exit)


    editmenu = Menu(menubar, tearoff = 0)
    menubar.add_cascade(label="Edit", menu=editmenu)

    editmenu.add_command(label="Undo", command=bn.undo)
    editmenu.add_command(label="Redo", command=bn.redo)
    editmenu.add_command(label="Delete all", command=bn.deleteall)

    ##auto_create_bn = Button(window, text = 'Auto create', command = auto_create)
    ##auto_create_bn.place(x = 450, y = 20)

    ##open_img_bn = Button(window, text = 'Open Image', command = open_img)
    ##open_img_bn.place(x = 520, y = 20)
    if(img_to_open is not None and seg is not None):
        bn.open_img(img_to_open)
        bn.auto_create(seg)
    window.config(menu = menubar)
    window.mainloop()


if __name__ == '__main__':
    run(linked = False)