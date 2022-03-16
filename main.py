from datetime import datetime
import shutil                                                                                    # import shutil, a library that provide high level file operations
from fastapi import FastAPI, UploadFile, File                                                    # import fastapi, used to create an api with versitile endpoints
import os                                                                                        # import os. used to navigate the folder structure           
import base64                                                                                    # import the base64 library to encode the file
from fastapi.responses import FileResponse                                                       # import the file response object
from rethinkdb import RethinkDB


app = FastAPI()                                                                                  # FastAPI initilizer
r = RethinkDB()

def unique(list1):
 
    # initialize a null list
    unique_list = []
     
    # traverse for all elements
    for x in list1:
        # check if exists in unique_list or not
        if x not in unique_list:
            unique_list.append(x)
    return unique_list

@app.get('/')
def root():
    return {
        "response":"200 Ok"
    }

@app.post('/upload')                                                                            # post upload route        
async def upload(file: UploadFile = File(...)):                                                 # upload file function

    content = await file.read()                                                                 # var storing file content in bytes
    filename = file.filename                                                                    # var storing filename
    mime = file.content_type
    path = f'http://192.168.1.5:8000/images/profile/{filename}'
    encodedMessage = base64.b64encode(content)                                                  # var storing filetype
    #size = await file.size()
                                                                                                # write bytes content into file and store on server
    with open(filename, 'wb') as buffer:
        buffer.write(content)
        buffer.close()
        await file.close()
                                                                                                
    if(os.path.exists(f'images/profile/{filename}')):                                           # check if image exists in the profile image directory and act

        os.remove(f'images/profile/{filename}')                                                 # remove the image from the profile image directory if it exists
        
        
    else:

         shutil.move(filename, 'images/profile/')                                               # move the uploaded image to the profile image directory
                                                                                                # describe the server response body
    return {
        "file_name": filename,
        "file_type": mime,
        "path": path,
        "encoded_image_bytes": encodedMessage
        #"size": size
    }

@app.get('/images/profile/{imagename}')                                                         # get image route - a get route that returns images saved on server
def getImage(imagename:str):
    return FileResponse(f"images/profile/{imagename}")

@app.get('/users')
def getUsers():

    r.connect( "localhost", 28015).repl()
    users = []
    cursor = r.table("users").run()
    for document in cursor:
        users.append(document)
    cursor.close()
    return users

@app.get('/users/{id}')
def getUser(id:str):

    r.connect( "localhost", 28015).repl()

    return r.db('test').table('users').get(f'{id}').run()

@app.get('/sentcount/{id}')
def countSent(id:str):
    messages = []
    r.connect('localhost',28015).repl()
    cursor = r.table("messages-analytics").filter(r.row["from"] == f"{id}").run()
    for document in cursor:
        messages.append(document)
    count = len(messages)
    cursor.close()
    return str(count)

@app.get('/recvcount/{id}')
def countSent(id:str):
    messages = []
    r.connect('localhost',28015).repl()
    cursor = r.table("messages-analytics").filter(r.row["to"] == f"{id}").run()
    for document in cursor:
        messages.append(document)
    count = len(messages)
    cursor.close()
    return str(count)

@app.get('/status/{id}')
def online(id:str):
    userdata = {}
    r.connect('localhost',28015).repl()
    user =  r.db('test').table('users').get(f'{id}').run()
    userdata = user
    return {
        "active": userdata['active'],
        "lastseen": userdata['last_seen']
    }

@app.post('/updatestatus/{id}')
def updateStatus(id:str):
    r.connect('localhost',28015).repl()
    r.table("users").filter(r.row['id'] == f"{id}").update({"last_seen": r.expr(datetime.now(r.make_timezone('+00:00')))}).run()
    return {"update": f'active time set to {datetime.now()}'}

@app.get("/countunread/{id}")
def countunread(id:str):
    messages = []
    messagesRead = []
    countReceipts = 0
    countMessages = 0
    countUnread = 0
    r.connect('localhost',28015).repl()
    cursor = r.table("messages-analytics").filter(r.row["to"] == f"{id}").run()

    for document in cursor:
        messages.append(document)

    cursor1 = r.table("receipts").filter(r.row["recipient"] == f"{id}").run()
    for document1 in cursor1:
        messagesRead.append(document1)

    countMessages = len(messages)
    countReceipts = len(messagesRead)

    if countReceipts == 0:
        return str(countMessages)
    elif countMessages == 0:
        return str(0)
    elif (countMessages-countReceipts) == 0:
        return str(0)
    else:
        return str(countReceipts)
    

@app.get("/chatcount/{id}")
def chatcount(id:str):
    messagesTo = []
    messagesFrom = []
    messagesFromId = []
    messagesToId = []
    count = 0
   
    r.connect('localhost',28015).repl()

    cursor1 = r.table("messages-analytics").filter(r.row["to"] == f"{id}").run()
    for document1 in cursor1:
        messagesTo.append(document1)
    
    cursor = r.table("messages-analytics").filter(r.row["from"] == f"{id}").run()
    for document in cursor:
        messagesFrom.append(document)

    for i in range(len(messagesTo)):
        messagesToId.append(messagesTo[i]['from'])

    for j in range(len(messagesFrom)):
        messagesFromId.append(messagesFrom[j]['to'])

    count = len(unique(messagesToId))
    
    return str(count)




    