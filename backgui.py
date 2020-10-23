from tkinter import *
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
        lo = np.array(label) 
        hi = np.array(label)
        imgc = img.copy()
        mask = cv2.inRange(imgc, lo, hi)
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if(area> 100):
                contour_th = []
                i = 0
                while(i < len(contour)):
                    contour_th.append(tuple(contour[i][0]))
                    i = i + 1
                contour_th = reduce(contour_th)
                canvas.create_polygon(contour_th, fill=rgb2hex(label[0], label[1], label[2]), outline='black', width=2, stipple = 'gray50', tag = "polygon")

class Buttons:
    def __init__(self, canvas, iid, img_height, img_width, window, lb):
        self.state = 1
        self.canvas = canvas
        self.window = window
        self.iid = iid
        self.img_width = img_width
        self.img_height = img_height
        self.point_radius = 4
        self.lb = lb



        
        self.selected_polygon = None
        self.selected_polygon_points = []
        self.selected_point = None
        self.undo_stack = deque([])
        self.redo_stack = deque([])
        self.new_coords = []
        self.coords = []
        self.coords_animate = []


        self.add_arr = [] ### used in add_point function
        self.index = None ### used in move_point function
        self.color = "white"


########Shortcuts#################

    def undo_shortcut(self, event):
        self.undo()

    def redo_shortcut(self, event):
        self.redo()

    def esc_shortcut(self, event):
        if(self.state == 7):
            for id in self.selected_polygon_points:
                self.canvas.delete(id)
            self.reset()
            #self.unbind_all()
            self.selected_polygon = None
            self.coords = []
            



###########Top left buttons operations###############

    def undo(self):
        self.unbind_all()
        self.reset()
        self.delete_selected_polygon_points()
        if(len(self.undo_stack)!=0):
            self.state = 1
            self.polygon = None
            self.coords = []
            self.new_coords = []
            op, id, coords, color = self.undo_stack.pop()
            if(op == 1):
                new_coords = self.canvas.coords(id)
                self.canvas.coords(id, coords)
                self.redo_stack.append([id, new_coords])
            elif(op == 2):
                id = self.canvas.create_polygon(coords, fill = color,  outline='black', width=2, stipple = 'gray50', tag = "polygon")
                self.redo_stack.append([2, id, coords, color])
            elif(op == 3):
                self.canvas.delete(id)
                self.redo_stack.append([3, id, coords, color])


    def redo(self):
        self.unbind_all()
        self.reset()
        self.delete_selected_polygon_points()
        if(len(self.redo_stack)!=0):
            
            id, self.coords = self.redo_stack.pop()
            self.new_coords = self.canvas.coords(id)
            self.canvas.coords(id, self.coords)
            self.create_selected_polygon_points()
            self.undo_stack.append([id, self.new_coords])
    
    def deleteall(self):
        self.reset()
        self.delete_selected_polygon_points()
        self.unbind_all()
        for i in self.canvas.find_all():
            if(i!=self.iid):
                self.canvas.delete(i)

######Button functions#############
    
    
    def new(self):
        self.unbind_all()
        self.canvas.tag_unbind("polygon", "<Button-1>")
        self.reset()
        self.selected_polygon = None
        self.canvas.bind("<Motion>", self.animate_polygon_new)
        self.coords = []
        self.state = 7


    def select(self):
        self.unbind_all()
        self.reset()
        self.canvas.tag_bind("point", "<Button-1>", self.move_point_click)
        self.state = 1
    
    def delete(self):
        self.unbind_all()
        self.reset()
        self.canvas.tag_bind("point", "<Button-1>", self.move_point_click)
        if(self.selected_polygon!=None):
            self.redo_stack = []
            self.undo_stack.append([2 ,-1, self.coords, self.canvas.itemcget(self.selected_polygon, "fill")])
            self.canvas.delete(self.selected_polygon)
            self.delete_selected_polygon_points()
            self.state = 1
            self.selected_polygon = None
            self.coords = []

    def add_p(self):
        self.unbind_all()
        self.reset()
        self.new_coords = []
        self.add_arr = []
        if(self.selected_polygon!=None):
            self.state = 2

    def move_p(self):
        self.unbind_all()
        self.reset()
        self.canvas.tag_bind("point", "<Button-1>", self.move_point_click)
        if(self.selected_polygon!=None):
            self.state = 3

    def rm_p(self):
        self.reset()
        self.unbind_all()
        self.state = 5

    def inc(self):
        self.unbind_all()
        self.reset()
        self.canvas.tag_bind("point", "<Button-1>", self.move_point_click)
        self.canvas.lift(self.selected_polygon)
        for point in self.selected_polygon_points:
            self.canvas.lift(point)
        self.canvas.lower(self.iid)

    def dec(self):
        self.unbind_all()
        self.reset()
        self.canvas.tag_bind("point", "<Button-1>", self.move_point_click)
        self.canvas.lower(self.selected_polygon)
        for point in self.selected_polygon_points:
            self.canvas.lift(point)
        self.canvas.lower(self.iid)



    def save(self):
        list = self.canvas.find_all()
        self.reset()
        img = Image.new('RGB', (self.img_width, self.img_height), color = 'black')
        img1 = ImageDraw.Draw(img) 
        for i in list:
            if(self.canvas.itemcget(i, "tag") == "polygon"):
                coord = self.canvas.coords(i)
                color = self.canvas.itemcget(i, 'fill')
                img1.polygon(coord, fill = color, outline = color)  
        file_path = asksaveasfilename(parent=self.window, initialdir=os.getcwd(), title="Please select a file name for saving:")
        img.save(file_path)

    def backend(self, event):
        if(self.state == 1):
           self.select_polygon(event)
        elif(self.state == 2):
            self.add_point(event)
        elif self.state == 3:
             self.select_point(event)
        elif self.state == 4:
            self.move_point(event)
        elif self.state == 5:
            self.remove_point(event)
        elif self.state == 7:
            self.create_polygon(event)


    
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

    def animate_point_add(self, event):
        self.coords_animate = self.coords.copy()
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.coords_animate.append(x)
        self.coords_animate.append(y)
        self.canvas.coords(self.selected_polygon, self.coords_animate)
        if(self.selected_point == None):
            self.selected_point = self.canvas.create_oval(x-self.point_radius, y-self.point_radius, x+self.point_radius, y+self.point_radius, fill = "white", tag = "point")
        else:
            self.canvas.coords(self.selected_point, x-self.point_radius, y-self.point_radius, x+self.point_radius, y+self.point_radius)

        
    def animate_point_move(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.coords = self.canvas.coords(self.selected_polygon)
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



    def create_polygon(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.coords.append(x)
        self.coords.append(y)
        if(self.selected_polygon == None):
            self.redo_stack = []
            self.selected_polygon = self.canvas.create_polygon(self.coords, fill = self.color,  outline='black', width=2, stipple = 'gray50', tag = "polygon")
            self.undo_stack.append([3 , self.selected_polygon, self.coords, self.canvas.itemcget(self.selected_polygon, "fill")])
        else:
            self.redo_stack = []
            self.undo_stack.append([1 , self.selected_polygon, self.coords[:-2], self.canvas.itemcget(self.selected_polygon, "fill")])
            self.canvas.coords(self.selected_polygon, self.coords)
        self.selected_polygon_points.append(self.canvas.create_oval(x - self.point_radius, y-self.point_radius, x+self.point_radius, y+self.point_radius, fill = "white", tag = "point"))
        



    def add_point(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.coords = self.canvas.coords(self.selected_polygon)

        mind = 10
        mini = -1
        if(len(self.add_arr) < 2):
            for i in range(0, len(self.coords), 2):
                if(dis([x,y], [self.coords[i], self.coords[i+1]]) < mind):
                    mind = dis([x,y], [self.coords[i], self.coords[i+1]])
                    mini = i
            if(mini!=-1 and (len(self.add_arr) != 1 or ( len(self.add_arr) == 1 and mini!=self.add_arr[-1] ))):
                self.add_arr.append(mini)
            if(len(self.add_arr) == 2):
                small = min(self.add_arr[0], self.add_arr[1])
                big = max(self.add_arr[0], self.add_arr[1])
                temp = big-small+1
                self.new_coords = []
                if(temp > len(self.coords) - temp+ 2):
                    for i in range(small, big+2, 1):
                        self.new_coords.append(self.coords[i%len(self.coords)])
                else:
                    i = big + 2
                    self.new_coords.append(self.coords[big])
                    self.new_coords.append(self.coords[big+1])
                    while(i != small + 2):
                        self.new_coords.append(self.coords[i%len(self.coords)])
                        i = (i+1)%len(self.coords)
                self.coords = self.new_coords.copy()
                self.canvas.bind("<Motion>", self.animate_point_add)
        else:
            self.unbind_all()
            self.new_coords.append(x)
            self.new_coords.append(y)
            self.delete_selected_polygon_points()
            self.canvas.delete(self.selected_point)
            self.redo_stack.clear()
            self.undo_stack.append([1, self.selected_polygon, self.coords, self.canvas.itemcget(self.selected_polygon, "fill")])
            self.canvas.coords(self.selected_polygon, self.new_coords)
            self.create_selected_polygon_points()
            self.add_arr = []
            self.new_coords = []
            self.canvas.tag_bind("point", "<Button-1>", self.move_point_click)
            self.canvas.tag_bind("polygon", '<Button-1>', self.double_click)

    def remove_point(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.coords = self.canvas.coords(self.selected_polygon)
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
            self.redo_stack.clear()
            self.undo_stack.append([1, self.selected_polygon, self.coords, self.canvas.itemcget(self.selected_polygon, "fill")])
            self.canvas.coords(self.selected_polygon, self.new_coords)
            self.create_selected_polygon_points()
            self.canvas.tag_bind("point", "<Button-1>", self.move_point_click)
            self.state = 1
            
    def select_point(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.coords = self.canvas.coords(self.selected_polygon)
        self.new_coords = self.coords.copy()
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
            self.state = 4
            self.canvas.bind('<Motion>', self.animate_point_move)

    def move_point(self, event):
        self.selected_point = None
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.unbind_all()
        if(self.index!=None):
            self.new_coords = []
            #self.coords = self.canvas.coords(self.selected_polygon)
            self.undo_stack.append([1, self.selected_polygon, self.coords, self.canvas.itemcget(self.selected_polygon, "fill")])
            for i in range(self.index):
                self.new_coords.append(self.coords[i])
            self.new_coords.append(x)
            self.new_coords.append(y)
            for i in range(self.index+2, len(self.coords)):
                self.new_coords.append(self.coords[i])
            self.redo_stack.clear()
            self.canvas.coords(self.selected_polygon, self.new_coords)
        self.state = 3
        self.index = None
        self.canvas.tag_bind("point", "<Button-1>", self.move_point_click)

#########Mouse actions###########

    def move_point_click(self, event):
        self.unbind_all()
        self.state = 3
    
    def double_click(self, event):
        self.state = 1

    def unbind_all(self):
        self.canvas.unbind("<Motion>")
        self.canvas.tag_unbind("point", "<Button-1>")
        #self.canvas.tag_unbind("polygon", "<Button-1>")

######### Misc ##################
    def reset(self):
        if(self.selected_polygon!=None and len(self.coords)!=0):
            self.canvas.coords(self.selected_polygon, self.coords)
        if(self.selected_point!=None):
            self.canvas.delete(self.selected_point)
            self.selected_point = None

    def get_color(self, event):
        self.color = self.lb.get(self.lb.curselection())






