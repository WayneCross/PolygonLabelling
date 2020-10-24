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
    def __init__(self, canvas, iid, img_height, img_width, window, lb):
        self.state = 1
        self.canvas = canvas
        self.window = window
        self.iid = iid
        self.img_width = img_width
        self.img_height = img_height
        self.point_radius = 4
        self.lb = lb
        self.eventx = 0
        self.eventy = 0


        self.window.bind('<Control-z>', self.undo_shortcut)
        self.window.bind('<Control-y>', self.redo_shortcut)

        self.point_popup = Menu(self.window, tearoff = 0)
        self.point_popup.add_command(label ="Delete Point", command = self.delete_point)  


        self.polygon_popup = Menu(self.window, tearoff = 0)
        self.polygon_popup.add_command(label ="Knife", command = self.use_knife)  
        self.polygon_popup.add_command(label ="Bring in front", command = self.inc)  
        self.polygon_popup.add_command(label ="Send to back", command = self.dec)  
        self.polygon_popup.add_command(label ="Delete Polygon", command = self.delete_polygon)  

        
        self.selected_polygon = None
        self.selected_polygon_points = []
        self.selected_point = None
        self.undo_stack = deque([])
        self.redo_stack = deque([])
        self.new_coords = []
        self.coords = []
        self.coords_animate = []


        self.index = None ### used in move_point function
        self.color = "white"

        self.edit_mode()


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
        self.reset()
        self.delete_selected_polygon_points()
        if(self.state == 1):
            self.edit_mode()
        else:
            self.create_mode()


    def redo(self):
        self.reset()
        self.delete_selected_polygon_points()
        if(self.state == 1):
            self.edit_mode()
        else:
            self.create_mode()
    
    def deleteall(self):
        self.reset()
        self.delete_selected_polygon_points()
        for i in self.canvas.find_all():
            if(i!=self.iid):
                self.canvas.delete(i)
        self.edit_mode()

######Button functions#############
    




    def inc(self):
        self.canvas.lift(self.selected_polygon)
        for point in self.selected_polygon_points:
            self.canvas.lift(point)
        self.canvas.lower(self.iid)

    def dec(self):
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
            self.selected_polygon = self.canvas.create_polygon(self.coords, fill = self.color,  outline='black', width=2, stipple = 'gray50', tag = "polygon")
        else:
            self.canvas.coords(self.selected_polygon, self.coords)
        self.selected_polygon_points.append(self.canvas.create_oval(x - self.point_radius, y-self.point_radius, x+self.point_radius, y+self.point_radius, fill = "white", tag = "point"))
        



    


            
    def delete_point(self):
        x = self.eventx
        y = self.eventy
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
            self.state = 1


    def select_point(self, event):
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
        self.selected_point = None
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if(self.index!=None):
            self.new_coords = []
            self.undo_stack.append([1, self.selected_polygon, self.coords, self.canvas.itemcget(self.selected_polygon, "fill")])
            for i in range(self.index):
                self.new_coords.append(self.coords[i])
            self.new_coords.append(x)
            self.new_coords.append(y)
            for i in range(self.index+2, len(self.coords)):
                self.new_coords.append(self.coords[i])
            self.redo_stack.clear()
            self.canvas.coords(self.selected_polygon, self.new_coords)
        self.index = None
        self.canvas.unbind('<Motion>')
        self.canvas.tag_bind("point", "<Button-1>", self.select_point)
        self.coords = self.new_coords
        self.edit_mode()
        self.create_selected_polygon_points()

    def delete_polygon(self):
        self.delete_selected_polygon_points()
        self.canvas.delete(self.selected_polygon)

    def knife(self, event):
        print("A")
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.coords = self.canvas.coords(self.selected_polygon)
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

    def get_color(self, event):
        self.color = self.lb.get(self.lb.curselection())

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
        self.undo_stack.clear()
        self.redo_stack.clear()

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
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.canvas.bind("<Button-1>", self.create_polygon)
        self.canvas.bind("<Motion>", self.animate_polygon_new)

    def use_knife(self):
        self.canvas.tag_unbind("point", "<Button-1>")
        self.canvas.tag_unbind("point", "<Button-3>")
        self.canvas.tag_unbind("polygon", "<Button-1>")
        self.canvas.tag_unbind("polygon", "<Button-3>")
        self.canvas.bind("<Button-1>", self.knife)




