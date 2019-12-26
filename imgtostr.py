import base64
import sys

filee = input("Enter encode Filename: ")

finame = input("enter the file name to be written")
 
with open(filee, "rb") as imageFile:
    str = base64.b64encode(imageFile.read())
    print (str)
with open (finame,'wb') as file1:
    file1.write(str)
     
    
 

        
