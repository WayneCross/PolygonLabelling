from tkinter import *
from tkinter.colorchooser import askcolor
from tkinter.filedialog import asksaveasfilename, askopenfilename
from PIL import Image, ImageDraw, ImageTk
import os
from colormap import rgb2hex, hex2rgb
import numpy as np
from collections import deque
import numpy as np
import math
import cv2 as cv2
import json
from datetime import datetime
import tkinter as tk
import base64
import pickle
from io import BytesIO

def slope(a, b):
    return math.degrees(math.atan2((a[1]-b[1]),(a[0]-b[0])))

def dis(a, b):
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

def red1(li):
    if(len(li) < 2):
        return li
    ans = []
    ans.append(li[0])
    th =  10
    for i in range(1, len(li)):
        if(dis(ans[-1], li[i]) > th):
            ans.append(li[i])
    return ans

def red2(li):
    ans = [li[0]]
    for i in range(1, len(li)):
        if((ans[-1][0] == li[i][0] and li[i][0] == li[(i+1)%len(li)][0]) or (ans[-1][1] == li[i][1] and li[i][1] == li[(i+1)%len(li)][1])):
            continue
        ans.append(li[i])
    return ans

def red3(li, th):
    ans = [li[0]]
    for i in range(1, len(li)):
        if(slope(ans[-1], li[i]) == slope(li[i], li[(i+1)%len(li)])):
            continue
        if(abs(slope(ans[-1], li[i]) - slope(li[(i+1)%len(li)], li[(i+2)%len(li)])) < th):
            continue
        ans.append(li[i])
    return ans

def reduce(li):
    li = red1(li)
    li = red2(li)
    prev = len(li)
    while(True):
        li = red3(li, 10)
        if(prev == len(li)):
            break
        prev = len(li)
    return li


def get_labels(img):
    labels = []
    arr = np.zeros((256,256,256))
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            if(arr[img[i,j,0],img[i,j,1],img[i,j,2]] == 0):
                arr[img[i,j,0],img[i,j,1],img[i,j,2]]  = 1
                labels.append(img[i][j])
    return labels

def draw(canvas, labels, img):
    for label in labels:
        if(int(label[0]) + int(label[1]) + int(label[2]) == 0):
            continue
        if(255 - int(label[0]) + 255 - int(label[1]) + 255 - int(label[2]) < 126):
            continue
        lo = np.array(label) 
        hi = np.array(label)
        imgc = img.copy()
        mask = cv2.inRange(imgc, lo, hi)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE    )
        for contour in contours:
            area = cv2.contourArea(contour)
            #if(label[0] != img[x][y][0] or label[1] != img[x][y][1] or label[2] != img[x][y][2]):
            #    continue
            if(area> 100 ):
                contour_th = []
                i = 0
                while(i < len(contour)):
                    contour_th.append(tuple(contour[i][0]))
                    i = i + 1
                contour_th = reduce(contour_th)
                canvas.create_polygon(contour_th, fill=rgb2hex(label[0], label[1], label[2]), outline='black', width=2, stipple = 'gray50', tag = "polygon")

def shortest_dist(x, y, x1, y1, x2, y2):
    temp = 0
    if(x1 == x2):
        temp = 0.001
    b = 1
    a = -1 * (y1-y2)/(x1-x2 + temp)
    c = -1 * (a * x1 + b * y1)
    d = abs((a * x + b * y + c)) / (math.sqrt(a * a + b * b)) 
    temp = (-1 * (a * x + b * y + c) / (a * a + b * b))  
    xa = temp * a + x  
    ya = temp * b + y  
    return d, xa, ya

class Buttons:
    def __init__(self, canvas, iid, img_height, img_width, window, labels):
        self.state = 1
        self.canvas = canvas
        self.window = window
        self.iid = iid
        self.img_width = img_width
        self.img_height = img_height
        self.point_radius = 4
        self.labels = labels
        self.eventx = 0
        self.eventy = 0
        self.img = None

        self.window.bind('<Control-z>', self.undo_shortcut)
        self.window.bind('<Control-y>', self.redo_shortcut)

        self.point_popup = Menu(self.window, tearoff = 0)
        self.point_popup.add_command(label ="Delete Point", command = self.delete_point)  


        self.polygon_popup = Menu(self.window, tearoff = 0)
        self.polygon_popup.add_command(label ="Knife", command = self.use_knife)  
        self.polygon_popup.add_command(label ="Bring in front", command = self.inc)  
        self.polygon_popup.add_command(label ="Send to back", command = self.dec)  
        self.polygon_popup.add_command(label ="Delete Polygon", command = self.delete_polygon)  
        self.polygon_popup.add_command(label ="Change Color", command = self.edit_color)  

        
        self.selected_polygon = None
        self.selected_polygon_points = []
        self.selected_point = None
        self.undo_stack = deque([])
        self.redo_stack = deque([])
        self.new_coords = []
        self.coords = []
        self.coords_animate = []


        self.index = None ### used in move_point function
        self.color = "black"
        self.tcolor = self.color
        self.edit_mode()


        self.list = dict([])

       
        self.map = dict([])
########Shortcuts#################

    def undo_shortcut(self, event):
        self.undo()

    def redo_shortcut(self, event):
        self.redo()

    def esc_shortcut(self, event):
        for id in self.selected_polygon_points:
            self.canvas.delete(id)
        self.canvas.coords(self.selected_polygon, self.coords)
        self.canvas.delete(self.selected_point)
        self.selected_polygon = None
        self.coords = []
        self.new_coords = []
        self.coords_animate = []
        if(self.state == 1):
            self.edit_mode()
            self.create_selected_polygon_points()
        else:
            self.create_mode()
            



###########Top left buttons operations###############

    def undo(self):
        self.button_break()
        if(len(self.undo_stack)!=0):
            self.delete_selected_polygon_points()
            cur = self.undo_stack[-1]
            self.undo_stack.pop()
            if(cur[0]!="delete all"):
                while(self.map.get(cur[1], cur[1])!=cur[1]):
                    cur[1] = self.map.get(cur[1], cur[1])
            if(cur[0] == "move"):
                self.redo_stack.append(["move", cur[1], self.canvas.coords(cur[1]), cur[2]])
                self.canvas.coords(cur[1], cur[2])
            elif(cur[0] == "delete polygon"):
                self.redo_stack.append(["delete polygon", cur[1], cur[2], cur[3], cur[4]])
                self.selected_polygon = self.canvas.create_polygon(cur[2], fill = cur[3],  outline='black', width=2, stipple = 'gray50', tag = "polygon")
                c = cur[4]
                while(c in self.map.keys()):
                    c = self.map[c]
                self.canvas.lift(self.selected_polygon, c)
                self.create_selected_polygon_points()
                self.map[cur[1]] = self.selected_polygon
                self.delete_selected_polygon_points()
            elif(cur[0] == "inc"):
                while(self.map.get(cur[2], cur[2])!=cur[2]):
                    cur[2] = self.map.get(cur[2], cur[2])
                self.redo_stack.append(["inc", cur[1], cur[2], cur[3]])
                self.canvas.lower(cur[1], cur[2])
            elif(cur[0] == "dec"):
                while(self.map.get(cur[2], cur[2])!=cur[2]):
                    cur[2] = self.map.get(cur[2], cur[2])
                self.canvas.lift(cur[1], cur[2])
                self.redo_stack.append(["dec", cur[1], cur[2], cur[3]])
            elif(cur[0] == "delete point"):
                self.redo_stack.append(["delete point", cur[1], self.canvas.coords(cur[1])])
                self.canvas.coords(cur[1], cur[2])
            elif(cur[0] == "knife"):
                self.redo_stack.append(["knife", cur[1], self.canvas.coords(cur[1])])
                self.canvas.coords(cur[1], cur[2])
            elif(cur[0] == "createnew"):
                self.redo_stack.append(["createnew", cur[1], cur[2], cur[3]])
                self.canvas.delete(cur[1])
            elif(cur[0] == "createedit"):
                self.redo_stack.append(["createedit", cur[1], self.canvas.coords(cur[1])])
                self.canvas.coords(cur[1], cur[2])
            elif(cur[0] == "delete all"):
                temp = []
                for i, coords, colour in cur[1]:
                    self.map[i] = self.canvas.create_polygon(coords, fill = colour,  outline='black', width=2, stipple = 'gray50', tag = "polygon")
                    temp.append([i, coords, colour])
                self.redo_stack.append(["delete all", temp])
            elif(cur[0] == "color edit"):
                self.redo_stack.append(cur)
                self.canvas.itemconfig(cur[1], fill = cur[2])
            self.selected_polygon = cur[1]
            self.create_selected_polygon_points()

        


    def redo(self):
        self.button_break()
        if(len(self.redo_stack)!=0):
            self.delete_selected_polygon_points()
            cur = self.redo_stack[-1]
            self.redo_stack.pop()
            if(cur[0] != "delete all"):
                while(self.map.get(cur[1], cur[1])!=cur[1]):
                    cur[1] = self.map.get(cur[1], cur[1])
            if(cur[0] == "move"):
                self.undo_stack.append(["move", cur[1], cur[3]])
                self.canvas.coords(cur[1], cur[2])
            elif (cur[0] == "delete point"):
                self.undo_stack.append(["delete point", cur[1], self.canvas.coords(cur[1])])
                self.canvas.coords(cur[1], cur[2])
            elif (cur[0] == "inc"):
                temp = self.canvas.find_above(self.canvas.find_above(cur[1]))
                self.undo_stack.append(["inc", cur[1], self.canvas.find_below(cur[1]), temp])
                self.canvas.lift(cur[1], temp)
                self.canvas.lower(self.iid)
            elif (cur[0] == "dec"):
                temp = self.canvas.find_below(self.canvas.find_below(cur[1]))
                self.undo_stack.append(["dec", cur[1], self.canvas.find_above(cur[1]), temp])
                self.canvas.lower(cur[1], temp)
                self.canvas.lower(self.iid)
            elif (cur[0] == "knife"):
                self.undo_stack.append(["knife", cur[1], self.canvas.coords(cur[1])])
                self.canvas.coords(cur[1], cur[2])
            elif(cur[0] == "createnew"):
                temp = self.canvas.create_polygon(cur[2], fill = cur[3],  outline='black', width=2, stipple = 'gray50', tag = "polygon")
                self.map[cur[1]] = temp
                cur[1] = temp
                self.undo_stack.append(["createnew", cur[1], cur[2], cur[3]])
            elif(cur[0] == "createedit"):
                self.undo_stack.append(["createedit", cur[1], self.canvas.coords(cur[1])])
                self.canvas.coords(cur[1], cur[2])
            elif(cur[0] == "delete polygon"):
                self.undo_stack.append(["delete polygon", cur[1], cur[2], cur[3], cur[4]])
                self.canvas.delete(cur[1])
            elif(cur[0] == "delete all"):
                self.deleteall()
            elif(cur[0] == "color edit"):
                self.undo_stack.append(cur)
                self.canvas.itemconfig(cur[1], fill = cur[3])
            self.selected_polygon = cur[1]
            self.create_selected_polygon_points()

    
    def deleteall(self):
        self.reset()
        self.delete_selected_polygon_points()
        cur = []
        for i in self.canvas.find_all():
            if(i!=self.iid):
                cur.append([i, self.canvas.coords(i), self.canvas.itemcget(i, "fill")])
                self.canvas.delete(i)
        self.undo_stack.append(["delete all", cur])

######Button functions#############
    




    def inc(self):
        self.redo_stack.clear()
        temp = self.canvas.find_above(self.canvas.find_above(self.selected_polygon))
        self.undo_stack.append(["inc", self.selected_polygon, self.canvas.find_below(self.selected_polygon), temp])
        self.canvas.lift(self.selected_polygon, temp)
        for point in self.selected_polygon_points:
            self.canvas.lift(point)
        self.canvas.lower(self.iid)
        

    def dec(self):  
        self.redo_stack.clear()
        temp = self.canvas.find_below(self.canvas.find_below(self.selected_polygon))
        self.undo_stack.append(["dec", self.selected_polygon, self.canvas.find_above(self.selected_polygon), temp])
        self.canvas.lower(self.selected_polygon, temp)
        for point in self.selected_polygon_points:
            self.canvas.lift(point)
        self.canvas.lower(self.iid)
        



    def export(self):
        list = self.canvas.find_all()
        self.reset()
        img = Image.new('RGB', (self.img.size[0], self.img.size[1]), color = 'black')
        img1 = ImageDraw.Draw(img)
        for i in list:
            if(self.canvas.itemcget(i, "tag") == "polygon"):
                coord = self.canvas.coords(i)
                color = self.canvas.itemcget(i, 'fill')
                if(len(coord) > 2):
                    img1.polygon(coord, fill = color, outline = color)  
        
        file_path = asksaveasfilename(parent=self.window, initialdir=os.getcwd(), title="Please select a file name for saving:", defaultextension="*.png", filetypes=[("PNG file", "*.png")])
        if(file_path!=""):
            img.save(file_path)

    def save(self):
        data = dict([])
        for id in self.canvas.find_all():
            if(id!=self.iid and self.canvas.itemcget(id, "tag") == "polygon"):
                data[id] = [self.canvas.itemcget(id, "fill"), self.canvas.coords(id)]
        files = [('JSON File', '*.json')]
        file_path = asksaveasfilename(parent=self.window, initialdir=os.getcwd(), title="Please select a file name for saving:", defaultextension = json, filetypes = files)
        if(file_path is None or file_path == ""):
            return
        with open(file_path, 'w') as outfile:
            self.img.save(file_path[:-4]+'jpg')
            json.dump(data, outfile)

    def load(self):
        files = [('JSON File', '*.json')]
        filename = askopenfilename(parent=self.window, initialdir = os.getcwd(),title = "Select file",defaultextension = json, filetypes = files)
        if(filename is None or filename == ""):
            return
        for id in self.canvas.find_all():
            if(id!=self.iid):
                self.canvas.delete(id)
        with open(filename, 'r') as fp:
            data = json.load(fp)
        
        self.img = Image.open(filename[:-4]+'jpg') 
        img_height = self.img.size[1]
        img_width = self.img.size[0] 
        self.imgtk = ImageTk.PhotoImage(self.img)
        height = min(700, img_height)
        width = min(1250, img_width)
        self.canvas.configure(scrollregion=(0, 0, img_width, img_height ))
        self.canvas.configure(height = height, width = width)
        self.iid = self.canvas.create_image( img_width/2, img_height/2, image = self.imgtk )
        for color, coords in data.values():
            self.canvas.create_polygon(coords, fill = color,  outline='black', width=2, stipple = 'gray50', tag = "polygon")
    
###### points selected polygon functions#########
    
    def delete_selected_polygon_points(self):
        for id in self.selected_polygon_points:
            self.canvas.delete(id)

    def create_selected_polygon_points(self):
        if(self.selected_polygon is not None):
            self.selected_polygon_points = []
            self.coords = self.canvas.coords(self.selected_polygon)
            for i in range(0, len(self.coords), 2):
                self.selected_polygon_points.append(self.canvas.create_oval(self.coords[i] - self.point_radius, self.coords[i+1]-self.point_radius, self.coords[i]+self.point_radius, self.coords[i+1]+self.point_radius, fill = "white", tag = "point"))
    
######Animation functions###

    def animate_polygon_new(self, event):
        if(self.selected_polygon is not None):
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            self.coords_animate = self.coords.copy()
            self.coords_animate.append(x)
            self.coords_animate.append(y)
            self.canvas.coords(self.selected_polygon, self.coords_animate)

        
    def animate_point_move(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.coords_animate = self.coords.copy()
        self.coords_animate[self.index] = x
        self.coords_animate[self.index+1] = y
        self.canvas.coords(self.selected_polygon, self.coords_animate)
        self.canvas.coords(self.selected_point, x-self.point_radius, y - self.point_radius, x + self.point_radius, y + self.point_radius)



##########Operations ###############

    def select_polygon(self, event): ##### Used to select when selection tool
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        for point in self.selected_polygon_points:
            self.canvas.delete(point)
        self.selected_polygon = self.canvas.find_closest(x, y)[0]
        if(self.selected_polygon == self.iid):
            self.selected_polygon = None
        self.create_selected_polygon_points()
        color = self.canvas.itemcget(self.selected_polygon, "fill")
        for value in list(self.list.values()):
            if(color == rgb2hex(value[0][0], value[0][1], value[0][2])):
                self.lb.selection_clear(0, END)
                self.lb.selection_set(value[1])
                self.color = color
                break




    def create_polygon(self, event):
        self.redo_stack.clear()
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.new_coords.append(x)
        self.new_coords.append(y)
        if(self.selected_polygon == None):
            self.selected_polygon = self.canvas.create_polygon(self.new_coords, fill = self.color,  outline='black', width=2, stipple = 'gray50', tag = "polygon")
            self.undo_stack.append(["createnew", self.selected_polygon, self.new_coords.copy(), self.canvas.itemcget(self.selected_polygon, "fill")])
            
        else:
            self.canvas.coords(self.selected_polygon, self.new_coords)
            self.undo_stack.append(["createedit", self.selected_polygon, self.coords])
        self.selected_polygon_points.append(self.canvas.create_oval(x - self.point_radius, y-self.point_radius, x+self.point_radius, y+self.point_radius, fill = "white", tag = "point"))
        self.coords = self.new_coords.copy()



    


            
    def delete_point(self):
        self.redo_stack.clear()
        x = self.eventx
        y = self.eventy
        self.coords = self.canvas.coords(self.selected_polygon)
        self.undo_stack.append(["delete point", self.selected_polygon, self.coords])
        self.new_coords = []
        mind = 10
        mini = -1
        for i in range(0, len(self.coords), 2):
            if(dis([x,y], [self.coords[i], self.coords[i+1]]) < mind):
                mind = dis([x,y], [self.coords[i], self.coords[i+1]])
                mini = i
        if(mini!=-1):
            for i in range(mini):
                self.new_coords.append(self.coords[i])
            for i in range(mini+2, len(self.coords)):
                self.new_coords.append(self.coords[i])
            self.delete_selected_polygon_points()
            self.canvas.coords(self.selected_polygon, self.new_coords)
            self.create_selected_polygon_points()
            self.state = 1


    def select_point(self, event):
        self.redo_stack.clear()
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.coords = self.canvas.coords(self.selected_polygon)
        mind = 10
        mini = -1
        for i in range(0, len(self.coords), 2):
            if(dis([x,y], [self.coords[i], self.coords[i+1]]) < mind):
                mind = dis([x,y], [self.coords[i], self.coords[i+1]])
                mini = i
        if(mini!=-1):
            self.index = mini
            mind = 10
            minp = -1
            for i in self.selected_polygon_points:
                pcoords = self.canvas.coords(i)
                if(dis([self.coords[mini], self.coords[mini+1]],[pcoords[0]+self.point_radius, pcoords[1]+self.point_radius] ) < mind):
                    mind = dis([self.coords[mini], self.coords[mini+1]],[pcoords[0]+self.point_radius, pcoords[1]+self.point_radius] ) 
                    minp = i
            self.selected_point = minp
            self.canvas.tag_unbind("point", "<Button-3>")
            self.canvas.bind('<Motion>', self.animate_point_move)
            self.canvas.tag_bind("point","<Button-1>", self.move_point)
            self.canvas.tag_unbind("polygon", "<Button-3>")

    def move_point(self, event):
        self.redo_stack.clear()
        self.selected_point = None
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if(self.index!=None):
            self.new_coords = []
            for i in range(self.index):
                self.new_coords.append(self.coords[i])
            self.new_coords.append(x)
            self.new_coords.append(y)
            for i in range(self.index+2, len(self.coords)):
                self.new_coords.append(self.coords[i])
            self.canvas.coords(self.selected_polygon, self.new_coords)
            self.undo_stack.append(["move", self.selected_polygon, self.coords])
        self.index = None
        self.canvas.unbind('<Motion>')
        self.canvas.tag_bind("point", "<Button-1>", self.select_point)
        self.coords = self.new_coords.copy()
        self.edit_mode()
        self.create_selected_polygon_points()

    def delete_polygon(self):
        self.redo_stack.clear()
        self.delete_selected_polygon_points()
        self.undo_stack.append(["delete polygon", self.selected_polygon, self.canvas.coords(self.selected_polygon), self.canvas.itemcget(self.selected_polygon, "fill"), self.canvas.find_below(self.selected_polygon)[0]])
        self.canvas.delete(self.selected_polygon)

    def knife(self, event):
        self.redo_stack.clear()
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.coords = self.canvas.coords(self.selected_polygon)
        self.undo_stack.append(["knife", self.selected_polygon, self.coords])
        mind = 20
        mini = -1
        mx = -1
        my = -1
        for i in range(0, len(self.coords), 2):
            x1 = self.coords[i]
            x2 = self.coords[(i+2)%len(self.coords)]
            y1 = self.coords[(i+1)%len(self.coords)]
            y2 = self.coords[(i+3)%len(self.coords)]
            dis,xa,ya = shortest_dist(x, y, x1, y1, x2, y2)
            if(dis < mind and ((x>=x1 and x<=x2) or (x<=x1 and x>=x2) or (y<=y1 and y>=y2) or (y>=y1 and y<=y2))):
                mini = i
                mind = dis
                mx = xa
                my = ya
        if(mini!=-1):
            self.new_coords = []
            for i in range(0, mini+2):
                self.new_coords.append(self.coords[i%len(self.coords)])
            self.new_coords.append(mx)
            self.new_coords.append(my)
            for i in range(mini+2, len(self.coords)):
                self.new_coords.append(self.coords[i])
            self.canvas.coords(self.selected_polygon, self.new_coords)
            self.coords = self.new_coords.copy()   
        self.delete_selected_polygon_points()
        self.edit_mode()
        self.create_selected_polygon_points()



#########Mouse actions###########



    def point_right_click(self, event): 
        self.eventx = self.canvas.canvasx(event.x)
        self.eventy = self.canvas.canvasy(event.y)
        try: 
            self.point_popup.tk_popup(event.x_root, event.y_root) 
        finally: 
            self.point_popup.grab_release() 

    def polygon_right_click(self, event): 
        self.eventx = self.canvas.canvasx(event.x) 
        self.eventy = self.canvas.canvasy(event.y)
        self.selected_polygon = self.canvas.find_closest(self.eventx, self.eventy)[0]
        self.delete_selected_polygon_points()
        self.create_selected_polygon_points()
        try: 
            self.polygon_popup.tk_popup(event.x_root, event.y_root) 
        finally: 
            self.polygon_popup.grab_release() 

######### Misc ##################
    def reset(self):
        if(self.selected_polygon!=None and len(self.coords)!=0):
            self.canvas.coords(self.selected_polygon, self.coords)
        if(self.selected_point!=None):
            self.canvas.delete(self.selected_point)
            self.selected_point = None

    def edit_mode(self):
        self.state = 1
        if(self.selected_polygon is not None and len(self.coords)!=0):
            self.canvas.coords(self.selected_polygon, self.coords)
            self.delete_selected_polygon_points()
        self.window.bind('<Escape>', self.esc_shortcut)
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<Motion>")

        self.canvas.tag_bind("point", "<Button-1>", self.select_point)
        self.canvas.tag_bind("point", "<Button-3>", self.point_right_click) 

        
        self.canvas.tag_bind("polygon", "<Button-1>", self.select_polygon)  
        self.canvas.tag_bind("polygon", "<Button-3>", self.polygon_right_click) 

    def edit_color(self):
        self.cwindow = Toplevel(self.window)
        self.cwindow.grab_set()
        self.cwindow.resizable(False, False)
        self.cwindow.geometry('300x200')
        self.color = self.canvas.itemcget(self.selected_polygon, "fill")
        #self.cwindow.attributes('-topmost', 'true')
        ok_color_bn = Button(self.cwindow, text = "Apply", command = self.color_apply_edit) 
        ok_color_bn.place(x = 20, y = 160)
        close_bn = Button(self.cwindow, text = "Close", command = self.on_closing) 
        close_bn.place(x = 70, y = 160)
        self.lbe = Listbox(self.cwindow, highlightcolor = None)
        self.lbe.place(x = 20, y = 15, height = 120)
        lpsb = Scrollbar(self.cwindow, command = self.lbe.yview)
        lpsb.place(x = 140, y = 15, height = 120)
        self.lbe.config(yscrollcommand = lpsb.set) 
        for key in self.list.keys():
            self.lbe.insert("end", key)
            self.lbe.itemconfig(self.lbe.size()-1, bg = rgb2hex(self.list[key][0][0], self.list[key][0][1], self.list[key][0][2]))
            self.lbe.itemconfig(self.lbe.size()-1, foreground = rgb2hex(255 - self.list[key][0][0], 255 - self.list[key][0][1], 255 - self.list[key][0][2]))
        self.lbe.select_set(0)
        self.ccanvas = Canvas(self.cwindow, height = 120, width = 100, bg = self.color)
        self.ccanvas.place(x = 170, y = 15)
        self.lbe.bind("<<ListboxSelect>>", self.lbcolor_apply)
        self.cwindow.protocol("WM_DELETE_WINDOW", self.on_closing)

    def color_apply_edit(self):
        self.undo_stack.append(["color edit", self.selected_polygon, self.canvas.itemcget(self.selected_polygon, "fill"), self.tcolor])
        self.color = self.tcolor
        self.canvas.itemconfig(self.selected_polygon, fill = self.color)
        self.on_closing()

    def color_apply(self):
        self.color = self.tcolor
        self.on_closing()

    def on_closing(self, event = None):
        self.lbe.unbind("<Button-1>")
        self.cwindow.grab_release()
        self.cwindow.destroy()

    


    def lbcolor_apply(self, event):
        self.tcolor = self.lbe.itemcget(self.lbe.curselection(), 'bg')
        self.ccanvas.configure(bg = self.tcolor )

    def choose_custom_color(self): 
        self.cwindow.attributes('-topmost', 'false')
        self.tcolor = colorchooser.askcolor(title ="Choose color")[1]
        self.ccanvas.configure(bg = self.tcolor )
        self.cwindow.attributes('-topmost', 'true')

    def create_mode(self):
        self.state = 2
        if(self.selected_polygon is not None and len(self.coords)!=0):
            self.canvas.coords(self.selected_polygon, self.coords)
            self.delete_selected_polygon_points()
        self.window.bind('<Escape>', self.esc_shortcut)
        self.canvas.tag_unbind("point", "<Button-1>")
        self.canvas.tag_unbind("point", "<Button-3>")
        self.canvas.tag_unbind("polygon", "<Button-1>")
        self.canvas.tag_unbind("polygon", "<Button-3>")
        self.canvas.bind("<Motion>", self.animate_polygon_new)
        self.delete_selected_polygon_points()
        self.selected_polygon = None
        self.coords = []
        self.new_coords = []
        self.canvas.bind("<Button-1>", self.create_polygon)

    def use_knife(self):
        self.canvas.tag_unbind("point", "<Button-1>")
        self.canvas.tag_unbind("point", "<Button-3>")
        self.canvas.tag_unbind("polygon", "<Button-1>")
        self.canvas.tag_unbind("polygon", "<Button-3>")
        self.canvas.bind("<Button-1>", self.knife)

    def button_break(self):
        if(len(self.coords)!=0):
            self.canvas.coords(self.selected_polygon, self.coords)
        self.delete_selected_polygon_points()
        self.create_selected_polygon_points()
        self.canvas.unbind("<Motion>")
        self.canvas.unbind("<Button-1>")
        if(self.state == 1):
            self.canvas.tag_bind("point", "<Button-1>", self.select_point)



    def create_new_color(self):
        self.cwindow = Toplevel(self.window)
        self.cwindow.resizable(False, False)
        self.cwindow.grab_set()
        self.cwindow.geometry('270x500')
        self.cwindow.attributes('-topmost', 'true')
        self.pcanvas = Canvas(self.cwindow, bg = "white", height = 240, width = 240)
        self.pcanvas.place(x = 10, y = 10)
        self.colorimg =  PhotoImage(file = "color_chooser.png")
        self.pcanvas.create_image(120, 120, image=self.colorimg)
        self.rscale = Scale(self.cwindow, from_=0, to=255, orient=HORIZONTAL, command = self.set_color)
        self.rscale.place(x = 10, y = 270)
        self.gscale = Scale(self.cwindow, from_=0, to=255, orient=HORIZONTAL, command = self.set_color)
        self.gscale.place(x = 10, y = 310)
        self.bscale = Scale(self.cwindow, from_=0, to=255, orient=HORIZONTAL, command = self.set_color)
        self.bscale.place(x = 10, y = 350)
        self.rscale.set(np.random.randint(0,256))
        self.gscale.set(np.random.randint(0,256))
        self.bscale.set(np.random.randint(0,256))
        self.ccanvas = Canvas(self.cwindow, height = 100, width = 100, bg = rgb2hex(self.rscale.get(), self.gscale.get(), self.bscale.get()))
        self.ccanvas.place(x = 150, y = 290)
        self.name = Entry(self.cwindow)
        self.name.place(x = 10, y = 400)
        apply_bn = Button(self.cwindow, text = "Create", command = self.apply_color)
        apply_bn.place(x = 10, y = 440)
        cancel_bn = Button(self.cwindow, text = "Cancel", command = self.lb_cancel)
        cancel_bn.place(x = 70, y = 440)
        self.lb.bind("<<ListboxSelect>>", self.lb_select)
        self.pcanvas.bind("<B1-Motion>", self.select_color)
        self.cwindow.protocol("WM_DELETE_WINDOW", self.lb_close)
        

    def select_color(self, event):
        x = event.x
        y = event.y
        if(x < 0 or y < 0 or y >= self.colorimg.height() or x >= self.colorimg.width()):
            return
        r,g,b = self.colorimg.get(x, y)
        self.rscale.set(r)
        self.gscale.set(g)
        self.bscale.set(b)

    def lb_select(self, event):
        self.color = self.lb.itemcget(ANCHOR, 'bg')
        
    def lb_cancel(self):
        self.lb_close()

    def set_color(self, event):
        self.ccanvas.configure(bg = rgb2hex(self.rscale.get(), self.gscale.get(), self.bscale.get()))
    
    def apply_color(self):
        if(self.name.get() != ""):
            if(self.name.get() not in self.list):
                self.list[self.name.get()] = [[self.rscale.get(), self.gscale.get(), self.bscale.get()], len(self.list)]
                self.lb.insert("end", self.name.get())
                self.lb.itemconfig(self.lb.size()-1, bg = rgb2hex(self.rscale.get(), self.gscale.get(), self.bscale.get()))
                self.lb.itemconfig(self.lb.size()-1, foreground = rgb2hex(255 - self.rscale.get(), 255 - self.gscale.get(), 255 - self.bscale.get()))
            else:
                index = self.list[self.name.get()][1]
                self.lb.itemconfig(index, bg = rgb2hex(self.rscale.get(), self.gscale.get(), self.bscale.get()))
                self.lb.itemconfig(index, foreground = rgb2hex(255 - self.rscale.get(), 255 - self.gscale.get(), 255 -self.gscale.get())) 
                self.list[self.name.get()] = [[self.rscale.get(), self.gscale.get(), self.bscale.get()], index]
            self.lb_close()

    def lb_close(self):
        self.cwindow.grab_release()
        self.cwindow.destroy()
    
    def save_new_list(self):
        filename = asksaveasfilename(parent=self.window, initialdir=os.getcwd(), title="Please select a file name for saving:", defaultextension="*.h5", filetypes=[("H5 file", "*.h5")])
        if(filename!=""):
            with open(filename, 'wb') as f:
                pickle.dump(self.list, f)

    def load_new_list(self):
        self.lb.delete('0','end')
        dic_name = askopenfilename(parent=self.window, initialdir = os.getcwd(),title = "Select file", defaultextension="*.h5", filetypes=[("H5 file", "*.h5")])
        if(dic_name == ""):
            return
        with open(dic_name, 'rb') as f:
            self.list = pickle.load(f)
        for key in self.list.keys():
            self.list[key] = [self.list[key][0], self.lb.size()]
            self.lb.insert("end", key)
            self.lb.itemconfig(self.lb.size()-1, bg = rgb2hex(self.list[key][0][0], self.list[key][0][1], self.list[key][0][2]))
            self.lb.itemconfig(self.lb.size()-1, foreground = rgb2hex(255 - self.list[key][0][0], 255 - self.list[key][0][1], 255 - self.list[key][0][2]))
        
    def clear_list(self):
        self.lb.unbind("<Button-1>")
        self.list.clear()
        self.lb.delete(0,'end')

class IORedirector(object):
    '''A general class for redirecting I/O to this Text widget.'''
    def __init__(self,file = "log.txt"):
        self.file = file
        #self.terminal = sys.stdout

class StdoutRedirector(IORedirector):
    '''A class for redirecting stdout to this Text widget.'''
    def write(self,str):
        with open(self.file, "a+") as fp:
            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            temp = dt_string+" : "+str
            fp.write(temp)
            sys.stdout.write(temp)

    def flush(self):
        pass


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
    
def im_2_b64(image):
    buff = BytesIO()
    image.save(buff, format="JPEG")
    img_str = base64.b64encode(buff.getvalue())
    return img_str
