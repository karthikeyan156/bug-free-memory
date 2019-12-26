fname = input("enter the file name:")

with open(fname,'rb') as file:   
 text = file.read()
print(text)


with open("st.txt",'wb') as file1:
   file1.write(text)
    
