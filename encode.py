from PIL import Image
def encode():
    name=input("enter img name with ext:")
    fname = input("enter the file name to be encrypted")
    img=Image.open(name)
    img.show()
    imgcpy=img.copy()
    with open(fname) as file:
        message=file.read()
    if len(message)==0:
        raise Exception("Data is empty")
    message+=" stp "
    mess8bit=To8bitBin(message)
    #print mess8bit
    getPix(mess8bit,imgcpy,name)
    print ("Encryption Complete")
    img=Image.open("new"+name[0:len(name)-3]+"png")
    img.show()
def To8bitBin(mess):
    binmess = [] 
    for i in mess: 
        binmess.append(format(ord(i), '08b'))
    return binmess

def getPix(mess8bit,img,name):
     pixelmap=img.load()
     i=j=0
     rgb=0
     for k in mess8bit:
          l=0
          while l<8:
              pixel=pixelmap[i,j]
              #print "pixelmap1:",pixelmap[i,j]
              #print "pixel:",pixel
              p=str(format(int(pixel[rgb]),'08b'))
              #print "p:",p
              newpix=p[0:6]+k[l:l+2]
              #print "newpix1:", newpix
              l+=2
              newpix=int(newpix,2)
              #print "newpix2:",newpix
              if rgb==0:
                  pixelmap[i,j]=(newpix,int(pixel[1]),int(pixel[2]))
              elif rgb==1:
                  pixelmap[i,j]=(int(pixel[0]),newpix,int(pixel[2]))
              else:
                  pixelmap[i,j]=(int(pixel[0]),int(pixel[1]),newpix)
              #print "pixelmap2:",pixelmap[i,j]
              if rgb==2:
                  rgb=0
              else:
                 rgb+=1
              j+=1
              if j==img.size[1]:
                  j=0
                  i+=1
                  
     img.save("new"+name[0:len(name)-3]+"png")
encode()



    
             
           
