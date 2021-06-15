from Tkinter import Tk, Label, Button, Entry
import Tkinter as tk
import tkFileDialog, tkMessageBox



class Demo1:
    def __init__(self, master):

        self.master = master
        self.master.title("Map Creator")
        self.frame = tk.Frame(self.master)
        self.newWindow=None
        Label(master, text="Width").grid(row=0)
        Label(master, text="Height").grid(row=1)

        self.e1 = Entry(master)
        self.e2 = Entry(master)

        self.e1.insert(tk.END,"10")
        self.e2.insert(tk.END,"10")


        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        self.newWinBut = tk.Button(self.master, text = 'New Map', width = 20, command = self.new_window)
        self.newWinBut.grid(row=2,column=0)
        self.saveBut = tk.Button(self.master, text='Save', width=20, command=self.save)
        self.saveBut.grid(row=2, column=1)
        #self.frame.pack()

    def new_window(self):
        if self.newWindow!=None:
            self.newWindow.destroy()
        self.newWindow = tk.Toplevel(self.master)
        self.app = Demo2(self.newWindow,width=int(self.e1.get()),height=int(self.e2.get()))

    def save(self):
        if self.newWindow==None:
            tkMessageBox.showwarning("Error", "No map to save!")
            return
        f = tkFileDialog.asksaveasfile(mode='w', defaultextension=".txt")
        if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            return

        text2save = self.app.to_string()
        f.write(text2save)
        f.close()  # `()` was missing.


class Demo2:
    def __init__(self, master,width=10,height=10):
        self.master=master
        #self.frame = tk.Frame(self.master)
        # self.quitButton = tk.Button(self.frame, text = 'Quit', width = 25, command = self.close_windows)
        # self.quitButton.pack()
        # self.frame.pack()
        self.master.configure(cursor="dot black white")
        self.width=width
        self.height=height
        self.active_color = 1
        self.code={0:"#",1:"W",2:"A",3:"G"}
        self.cols={0:"white",1:"black",2:"blue",3:"green"}
        self.size = 32
        self.arr = [[0 for i in range(width)] for j in range(height)]
        self.rect_arr = [[None for i in range(width)] for j in range(height)]
        self.canv=tk.Canvas(self.master,width=max(self.size*width,4*self.size),height=self.size*height+2.5*self.size)
        self.canv.pack()
        self.canv.bind("<ButtonPress-1>", self.p1)
        self.canv.bind("<B1-Motion>", self.m1)
        self.canv.bind("<ButtonRelease-1>", self.on_button_release)
        self.canv.bind("<ButtonPress-3>", self.p2)
        self.canv.bind("<B3-Motion>", self.m2)
        self.canv.bind("<ButtonRelease-3>", self.on_button_release)
        self.changed = [[False for i in range(width)] for j in range(height)]
        for i in range(height):
            for j in range(width):
                self.rect_arr[i][j]=self.canv.create_rectangle(self.size*j,self.size*i,self.size*(j+1),self.size*(i+1), fill="white")

                #self.canv.tag_bind(self.rect_arr[i][j],'<ButtonPress-1>',self.get_click_func(i,j))
                #self.canv.tag_bind(self.rect_arr[i][j], '<B1-Motion>', self.get_click_func(i, j))

        self.col_circle = [0,0,0,0]
        t=["Empty","Wall","Start","Goal"]
        for i in range(4):
            self.col_circle[i] = self.canv.create_arc(self.size*(2*i+1),int(self.size*(height+0.5)),self.size*(2*i+2),int(self.size*(height+1.5)),extent=359, fill=self.cols[i], outline="black")
            self.canv.create_text(self.size*(2*i+1.5),self.size*(height+2),text=t[i])
            self.canv.tag_bind(self.col_circle[i],'<ButtonPress-1>',self.get_col(i))

        #self.canv.config(cursor='arrow black red')
        #self.frame.pack()

    def get_col(self,num):
        def change_col(*args):
            if self.cols[num]=="black":
                self.master.configure(cursor="dot black white")
                self.active_color=num
            else:
                self.master.configure(cursor="dot %s black"%self.cols[num])
                self.active_color=num
        return change_col


    def change(self,i,j,val=None):
        if i<0 or j<0 or i>self.height-1 or j>self.width-1:
            return
        if self.changed[i][j]==False:
            if val==None:
                self.arr[i][j] = (self.arr[i][j] + 1) % 4
            else:
                self.arr[i][j] = val
            self.canv.itemconfig(self.rect_arr[i][j], fill=self.cols[self.arr[i][j]])
            self.changed[i][j]=True


    def get_click_func(self,i,j):
        def help_func(*args):
            self.arr[i][j]=(self.arr[i][j]+1)%4
            self.canv.itemconfig(self.rect_arr[i][j],fill=self.cols[self.arr[i][j]])
            #print("called")

        return help_func


    def p1(self,event):
        self.on_button_press(event,self.active_color)

    def m1(self,event):
        self.on_move_press(event,self.active_color)

    def p2(self,event):
        self.on_button_press(event,0)

    def m2(self,event):
        self.on_move_press(event,0)

    def on_button_press(self,event,val=None):
        self.start_x = event.x
        self.start_y = event.y
        self.change(int(self.start_y/self.size),int(self.start_x/self.size),val)

    def on_move_press(self, event,val=None):
        curX, curY = (event.x, event.y)
        self.change(int(curY / self.size), int(curX / self.size),val)

    def on_button_release(self, event):
        self.changed = [[False for i in range(self.width)] for j in range(self.height)]

    def to_string(self):
        return_string=""
        import os
        for row in self.arr:
            temp=""
            for col in row:
                temp+=self.code[col]
            temp+=os.linesep
            return_string+=temp
        return return_string[:-1]

    def close_windows(self):
        self.master.destroy()

def main():
    root = tk.Tk()
    app = Demo1(root)
    root.mainloop()

if __name__ == '__main__':
    main()

