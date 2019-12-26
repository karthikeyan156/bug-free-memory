def decrypt(text,s): 
    result = "" 
  
    # traverse text 
    for i in range(len(text)): 
        char = text[i] 
  
        # Encrypt uppercase characters 
        if (char.isupper()): 
            result += chr((ord(char) - s))
  
        # Encrypt lowercase characters 
        else: 
            result += chr((ord(char) - s))   
           
  
    return result 
  
#check the above function
fname = input("enter the file name to be encrypted")
with open(fname) as file:   

 text = file.read()
 
 
s = 4
print ("Text  : " + text) 
print ("Shift : " + str(s)) 
print ("Cipher: " + decrypt(text,s))
finame = input("enter the filename to store encoded file")
with open (finame,'w') as file1:
    
 file1.write(decrypt(text,s))
 
