from PIL import Image
def decode():
    name=input("enter img name")
    fname = input("enter the file name to store data:")
    print ("Decoding.....")
    img=Image.open(name)
    img.show()
    st=getPix(img)
    print ("Hidden message is: ",st[0:len(st)-5])
    with open(fname,"w") as file:
        file.write(st[0:len(st)-5])

def getPix(img):
    pixelmap=img.load()
    i=j=rgb=0
    f=1
    temp=""
    st=""
    while i<img.size[0]:
        while j<img.size[1]:
            pixel=pixelmap[i,j]
            #print "pixel:",pixel
            p=str(format(int(pixel[rgb]),'08b'))
            #print "p:",p
            rgb+=1
            temp+=p[6:8]
            #print "temp:",temp
            if rgb==3:
                rgb=0
            if f==4:
                num=int(temp, 2)
                #print "num:",num
                ch=chr(num)
                #print "ch:",ch
                st=st+ch
                #print "st:",st
                f=0
                temp=""
                num=check(st)
                if num==1:
                    return st
            f+=1
            j+=1    
        i+=1        
                
    return "No hidden message      "

def check(s):
    #print s
    if s[len(s)-5:len(s)]==" stp ":
        return 1
    else:
        return 0
decode()         
                
                
            
            
            
