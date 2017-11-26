import sys
import os
import Tkinter as tk
import tkFileDialog
import tkMessageBox
import ttk as ttk

#ask for the master file to extract parts from
while True:
    masterFile=raw_input("Please specify gcode file to slice into parts:\ne.g. hello_world.gcode and the file is inside the same folder as this script\n").strip()
    #check if the file is gcode file
    if masterFile.endswith(".gcode"):
        print "Gcode file detected."
        break
    else:
        print "None gcode file detected, please load only gcode file..."

#load file data into string
masterFileString=""
with open(masterFile, 'r') as mFile:
    masterFileString=mFile.read()
if masterFileString=="":
    print "No content loaded..."
    sys.exit()
masterFileStringSplit=masterFileString.split("\n")

#define functions
def addPartFunction():
    global partCounter 
    theName=nameEntry.get().strip()
    if theName=="":
        print "Must enter name for part"
        return
    theLayerStart=layerStartEntry.get().strip()
    if theLayerStart=="":
        print "Must enter a starting layer number"
        return
    theLayerStart=int(theLayerStart)
    theLayerEnd=layerEndEntry.get().strip()
    if theLayerEnd=="":
        theLayerEnd=totalLayers    #by default set the the end of the layers
    else:
        theLayerEnd=int(theLayerEnd)
    if theLayerEnd<theLayerStart:
        print "End layer must not be smaller than start layer..."
        return
    numberOfLayers=theLayerEnd-theLayerStart+1
    partHeight=numberOfLayers*layerHeight
    listOfPartsTable.insert("","end", values=(theName,theLayerStart,theLayerEnd,numberOfLayers,partHeight))
    partCounter+=1
    updateNameEntry(os.path.splitext(masterFile)[0]+"_part"+str(partCounter))
    if len(layerEndEntry.get())==0:
        updateLayerStartEntry("")
    else:
        updateLayerStartEntry(str(int(layerEndEntry.get().strip())+1)+"")
    updateLayerEndEntry("")
    layerEndEntry.focus_set()

def modHeader(newExtruderPos):
    global oriHeader
    modHeader=""
    oriHeaderSplit=oriHeader.split("\n")
    for line in oriHeaderSplit:
        if line.find("G92")!=-1:
            #replace the extruder position and continue append
            modHeader+="\nG92 E"+newExtruderPos
        else:
            modHeader+="\n"+line
    modHeader=modHeader[1:]
    return modHeader

oriHeader=""
oriFooter=""
def sliceButtonFunction():
    global oriHeader
    global oriFooter
    global modFooter
    global totalLayers
    #prompt save destination
    folder = tkFileDialog.askdirectory()
    if folder is None: # ask save as file return `None` if dialog closed with "cancel".
        return
    #extract original header and footer
    #header
    headCounter=0
    while True:
        if headCounter==(len(masterFileStringSplit)-1):
            break
        if masterFileStringSplit[headCounter]!=";LAYER:0":
            oriHeader+=masterFileStringSplit[headCounter]+"\n"
        else:
            break
        headCounter+=1
    #modified header (a function instead to set new Extruder position of G92)
    #
    #footer
    footerCounter=len(masterFileStringSplit)-1
    firstEncounter=False
    while True:
        if footerCounter<0:
            break
        currentLine=masterFileStringSplit[footerCounter]
        if currentLine!="M107":
            oriFooter=currentLine+"\n"+oriFooter
        elif currentLine=="M107":
            if firstEncounter==True:
                oriFooter=currentLine+"\n"+oriFooter
                firstEncounter=False
            else:
                oriFooter=masterFileStringSplit[footerCounter-1]+"\n"+currentLine+"\n"+oriFooter
                footerCounter-=2
                break
        footerCounter-=1
    #modified footer
    modFooter=""
    oriFooterSplit=oriFooter.split("\n")
    linesToDelete=[]
    footerCounter=0
    while footerCounter<len(oriFooterSplit):
        footerPhrase=oriFooterSplit[footerCounter]
        if footerPhrase.find("M140")!=-1:
            linesToDelete.append(footerCounter)
            break
        footerCounter+=1
    for index,line in enumerate(oriFooterSplit):
        foundDel=False
        for delNum in linesToDelete:
            if index==delNum:
                foundDel=True
                break
        if foundDel==False:
            modFooter+="\n"+line
    modFooter=modFooter[1:]
    #procure the list of parts to be sliced
    partList=[]
    for item in listOfPartsTable.get_children():
        partList.append(listOfPartsTable.item(item)["values"])
    partList.sort(key=lambda x: x[2])   #sort part list by starting layer
    previousExtruderPos=-1
    for part in partList:
        thisGcode=""
        if part[1]==1:
            #the first part
            thisGcode=oriHeader+getLayersGcode(part[1],part[2])
            thisGcode+=modFooterF(str(float(getEndExtruderPos(thisGcode))-0.800))
            previousExtruderPos=getEndExtruderPos(thisGcode)
        elif part[2]==totalLayers:
            #the final part
            thisGcode=modHeader(previousExtruderPos)+getLayersGcode(part[1],part[2])+oriFooter
        elif part[1]>1 and part[2]<totalLayers:
            #the parts in the middle
            thisGcode=modHeader(previousExtruderPos)+getLayersGcode(part[1],part[2])
            thisGcode+=modFooterF(str(float(getEndExtruderPos(thisGcode))-0.800))
            previousExtruderPos=getEndExtruderPos(thisGcode)
        #export each files as gcodes after prompting save destination
        theFile=open(os.path.join(folder,part[0])+".gcode","w")
        theFile.write(thisGcode)
        theFile.close()
    tkMessageBox.showinfo("Save sliced parts", "Save succesful.")

def modFooterF(ePos):
    global modFooter
    modFooterSplit=modFooter.split("\n")
    bCounter=len(modFooterSplit)-1
    while bCounter>=0:
        line=modFooterSplit[bCounter]
        if line.find("G1 ")!=-1 and line.find(" E")!=-1:
            lineSplit=line.split(" E")
            modFooterSplit[bCounter]=lineSplit[0]+" E"+ePos
            break
        bCounter-=1
    jointModFooter=""
    for line in modFooterSplit:
        jointModFooter+="\n"+line
    return jointModFooter[1:]

def getEndExtruderPos(thisGcode):
    #look backward to find the final extruder position setting
    thisGcodeSplit=thisGcode.split("\n")
    backwardCounter=len(thisGcodeSplit)-1
    foundCounter=0
    while backwardCounter>=0:
        line=thisGcodeSplit[backwardCounter]
        if line.find("G1 ")!=-1 and line.find(" E")!=-1:
            foundCounter+=1
            if foundCounter==1:
                return line.split(" E")[1]
        backwardCounter-=1

def updateNameEntry(text):
    nameEntry.delete(0,tk.END)
    nameEntry.insert(0,text)
def updateLayerStartEntry(text):
    layerStartEntry.delete(0,tk.END)
    layerStartEntry.insert(0,text)
def updateLayerEndEntry(text):
    layerEndEntry.delete(0,tk.END)
    layerEndEntry.insert(0,text)

def getLayersGcode(start,end):
    #zero index correction
    start-=1
    end-=1
    #start
    layerGcodeStart=-1
    layerGcodeEnd=-1
    #seek for layers
    for index,line in enumerate(masterFileStringSplit):
        if line==";LAYER:"+str(start):
            layerGcodeStart=index
        elif line==";LAYER:"+str(end+1):
            layerGcodeEnd=index-1
        if layerGcodeStart!=-1 and layerGcodeEnd!=-1:
            break
    #layerGcodeEnd will still be -1 if it is the final part
    if layerGcodeEnd==-1:
        backCounter=len(masterFileStringSplit)-1
        while backCounter>=0:
            if masterFileStringSplit[backCounter]=="M107":
                layerGcodeEnd=backCounter-2
                break
            backCounter-=1
    #put into string
    layerGcode=""
    while layerGcodeStart<=layerGcodeEnd:
        layerGcode+=masterFileStringSplit[layerGcodeStart]+"\n"
        layerGcodeStart+=1
    return layerGcode

#launch the UI
root = tk.Tk()
root.minsize(500, 500)
root.maxsize(root.winfo_screenwidth(),root.winfo_screenheight())
root.protocol(name = "WM_DELETE_WINDOW",func=root.quit)
root.update()
root.title("Part Slicer - Evolve3D, Khai")
#theme
ttk.Style().theme_use("clam")
#GUI layout
#top frame for model info frame and add part frame
topFrame=tk.Frame(root)
#model info frame
modelInfoFrame=tk.Frame(topFrame)
#file name
fileNameFrame=tk.Frame(modelInfoFrame)
fileNameValue=tk.StringVar()
fileNameValue.set("File: "+os.path.splitext(masterFile)[0])
fileNameLabel=tk.Label(fileNameFrame,textvariable=fileNameValue)
fileNameLabel.pack(pady="5",padx="5",expand="1",side="left")
fileNameFrame.grid(in_=modelInfoFrame,row=1,column=0)
#total layers
totalLayersFrame=tk.Frame(modelInfoFrame)
totalLayersCount=tk.StringVar()
totalLayers=0
totalLayersLabel=tk.Label(totalLayersFrame,textvariable=totalLayersCount)
totalLayersLabel.pack(pady="5",padx="5",expand="1",side="left")
totalLayersFrame.grid(in_=modelInfoFrame,row=2,column=0)
#layer height
layerHeightFrame=tk.Frame(modelInfoFrame)
layerHeightValue=tk.StringVar()
layerHeight=0 #in mm
layerHeightLabel=tk.Label(layerHeightFrame,textvariable=layerHeightValue)
layerHeightLabel.pack(pady="5",padx="5",expand="1",side="left")
layerHeightFrame.grid(in_=modelInfoFrame,row=3,column=0)
#model height
modelHeightFrame=tk.Frame(modelInfoFrame)
modelHeightValue=tk.StringVar()
modelHeight=0
modelHeightLabel=tk.Label(modelHeightFrame,textvariable=modelHeightValue)
modelHeightLabel.pack(pady="5",padx="5",expand="1",side="left")
modelHeightFrame.grid(in_=modelInfoFrame,row=4,column=0)
#model info frame pack
modelInfoFrame.pack(padx="5",pady="5",side="left")

#read and place the model info data
counter=0
while counter<25:
    currentLine=masterFileStringSplit[counter]
    if currentLine.startswith(";Layer height:"):
        layerHeight=float(currentLine[15:])
        layerHeightValue.set("Layer Height: "+str(layerHeight)+" mm")
    elif currentLine.startswith(";LAYER_COUNT:"):
        totalLayers=int(currentLine[13:])
        totalLayersCount.set("Total Layers: "+str(totalLayers))
    counter+=1
modelHeight=layerHeight*totalLayers
modelHeightValue.set("Model Height: "+str(modelHeight)+" mm")

#add part frame
addPartFrame=tk.Frame(topFrame)
#Name label
nameLabelFrame=tk.Frame(addPartFrame)
nameLabel=tk.StringVar()
nameLabel.set("Name: ")
nameLabelLabel=tk.Label(nameLabelFrame,textvariable=nameLabel)
nameLabelLabel.pack(pady="5",padx="5",expand="1",side="left")
#Name entry
nameEntry=tk.Entry(nameLabelFrame)
partCounter=1
updateNameEntry(os.path.splitext(masterFile)[0]+"_part1")
nameEntry.pack(pady="5",padx="5",expand="1",side="left")
nameLabelFrame.grid(in_=addPartFrame,row=1,column=0)
#layer start label
layerStartFrame=tk.Frame(addPartFrame)
layerStart=tk.StringVar()
layerStart.set("Layer Start (inclusive): ")
layerStartLabel=tk.Label(layerStartFrame,textvariable=layerStart)
layerStartLabel.pack(pady="5",padx="5",expand="1",side="left")
#layer start entry
layerStartEntry=tk.Entry(layerStartFrame)
layerStartEntry.pack(pady="5",padx="5",expand="1",side="left")
layerStartFrame.grid(in_=addPartFrame,row=2,column=0)
#layer end label
layerEndFrame=tk.Frame(addPartFrame)
layerEnd=tk.StringVar()
layerEnd.set("Layer End (inclusive): ")
layerEndLabel=tk.Label(layerEndFrame,textvariable=layerEnd)
layerEndLabel.pack(pady="5",padx="5",expand="1",side="left")
#layer end entry
layerEndEntry=tk.Entry(layerEndFrame)
layerEndEntry.pack(pady="5",padx="5",expand="1",side="left")
layerEndFrame.grid(in_=addPartFrame,row=3,column=0)
#add part button
addPartButtonFrame=tk.Frame(addPartFrame)
addPartButton=tk.Button(addPartButtonFrame,text="Add Part",command=addPartFunction)
addPartButton.pack(pady="5",padx="5",expand="1",side="right")
addPartButtonFrame.grid(in_=addPartFrame,row=4,column=0)
#add part frame pack
addPartFrame.pack(padx="5",pady="5",side="right")
topFrame.pack(padx="5",pady="5",side="top")

#list of parts frame
listOfPartsFrame=tk.Frame(root)
#list of parts table
listOfPartsTable=ttk.Treeview(listOfPartsFrame)
listOfPartsTable["show"]="headings"
listOfPartsTable["columns"]=("Name","LayerStart","LayerEnd","NumberofLayers","PartHeight")
listOfPartsTable.heading("Name",text="Name")
listOfPartsTable.heading("LayerStart",text="Layer Start")
listOfPartsTable.heading("LayerEnd",text="Layer End")
listOfPartsTable.heading("NumberofLayers",text="Number of Layers")
listOfPartsTable.heading("PartHeight",text="Part Height")
listOfPartsTable.column("Name",minwidth=0,width=200, stretch="no",anchor="center")
listOfPartsTable.column("LayerStart",minwidth=0,width=100, stretch="no",anchor="center")
listOfPartsTable.column("LayerEnd",minwidth=0,width=100, stretch="no",anchor="center")
listOfPartsTable.column("NumberofLayers",minwidth=0,width=100, stretch="no",anchor="center")
listOfPartsTable.column("PartHeight",minwidth=0,width=150, stretch="no",anchor="center")
#scrollbar
listOfPartsScroll=ttk.Scrollbar(orient="vertical", command=listOfPartsTable.yview)
listOfPartsTable['yscroll'] = listOfPartsScroll.set
listOfPartsScroll.grid(in_=listOfPartsFrame, row=0, column=1, sticky="NS")
listOfPartsHScroll=ttk.Scrollbar(orient="horizontal", command=listOfPartsTable.xview)
listOfPartsTable['xscroll'] = listOfPartsHScroll.set
listOfPartsHScroll.grid(in_=listOfPartsFrame, row=1, column=0, sticky="EW")
listOfPartsTable.grid(in_=listOfPartsFrame, row=0, column=0, sticky="NSEW")
tk.Grid.columnconfigure(listOfPartsFrame,0,weight=1)
#list of parts frame pack
listOfPartsFrame.pack(padx="5",pady="5",side="top",fill="x")

#slice button
sliceButtonFrame=tk.Frame(root)
sliceButton=tk.Button(sliceButtonFrame,text="Slice",command=sliceButtonFunction)
sliceButton.pack(pady="5",padx="5",expand="1",side="left")
sliceButtonFrame.pack(padx="5",pady="5",side="bottom")

#synthesize GUI
root.mainloop()
root.destroy()