fname = input("enter the file name:")

with open(fname,'rb') as file:   
 text = file.read()
print(text)
str = text.decode("utf-8")
print(str)
with open("t.txt",'w') as file1:
   file1.write(str)
    
