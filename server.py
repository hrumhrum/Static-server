import socket
import threading
import os
import mimetypes
import rfc822
import time

MAX_THREADS=1000
cached_files={}
time_modif={}
date = rfc822.formatdate(time.time())
#print date
no_file="HTTP/1.1 404 Not Found\r\n"
no_file+="Server: myserver/0.0.1\r\n"
no_file+="Date: "+str(date)+"\r\n"
no_file+="Content-Type: text/html; charset=UTF-8\r\n"
no_file+="Connection: close\r\n\r\n"
no_file+="<html><head><title>404</title></head><body><h2>Page not found</h2></body></html>"

no_method= "HTTP/1.1 405 Method Not Allowed\r\n"
no_method+="Server: myserver/0.0.1\r\n"
no_method+="Date: "+str(date)+"\r\n"
no_method+="Content-Type: text/html; charset=UTF-8\r\n"
no_method+="Connection: close\r\n\r\n"
no_method+="<html><head><title>405</title></head><body><h2>Method Not Allowed</h2></body></html>"

not_modified="HTTP/1.1 304 Not Modified\r\n"
not_modified+="Server: myserver/0.0.1\r\n"
not_modified+="Date: "+str(date)+"\r\n"
not_modified+="Connection: close\r\n\r\n"

forbidden="HTTP/1.1 403 Forbidden\r\n"
forbidden+="Server: myserver/0.0.1\r\n"
forbidden+="Date: "+str(date)+"\r\n"
forbidden+="Content-Type: text/html; charset=UTF-8\r\n"
forbidden+="Connection: close\r\n\r\n"
forbidden+="<html><head><title>403</title></head><body><h2>Forbidden</h2></body></html>"

class workThread(threading.Thread):    
    def __init__(self):
        threading.Thread.__init__(self)

    def haveLowLevel(self,path):
        level=1
        temp = path.split('/')
        for f in range(len(temp)):
            if temp[f]=="..":
                level-=1
            else:
                level+=1
            if level<1:
                return True
        return False

    def encode(self,path):
        resp=""
        t=0
        for f in range(len(path)-2):
            if t!=0:
                t-=1
                continue
            if path[f]=='%':
                number = ord(path[f+1])-48
                number*=16
                if path[f+2]<='9':
                    number += ord(path[f+2])-ord('0')
                else:
                    number += ord(path[f+2])-ord('a')+10

                resp+=chr(number)
                t+=2
            else:
                resp+=path[f]
        if len(path)<2 or f+1==len(resp):
            return path
        else:
            if path[len(path)-3]!='%':
                resp+=path[len(path)-2:]
            return resp
    
    def run(self):
        while True:
            connection,client_address=sock.accept()
#            start=time.time()
            recv=connection.recv(1024)
            data=[]
            path=""
            method=""
            response=""
            lm=""
            canEncoding=False
            haveGz=False
            addIndex=False
            
            if len(recv)!=0:
                recv=recv.split('\n')
                for f in recv:
                    f=f.split(' ')
                    data.append(f)
                method=data[0][0]
                path=data[0][1]
                for f in range(2,len(data[0])-1):
                    path=path+' '+data[0][f]
                path=(path.split('?'))[0]
            else:
                connection.close()
            if method!="GET":
                response=no_method
 
            path=self.encode(path)
            
            for f in range(len(data)):
                if data[f][0]=="If-Modified-Since:":
                    for f1 in range(1,len(data[f])):
                        lm+=data[f][f1]+' '
                    break
                
            for f in range(len(data)):
                if data[f][0]=="Accept-Encoding:":
                    temp=data[f][1].split(',')
                    for f1 in temp:
                        if f1=="gzip":
                            canEncoding=True
                            break
                    break
                
            if len(lm)!=0:
                lm=lm[:len(lm)-2]
            
            if len(path)>0 and path[len(path)-1]=='/':
                path=path[:len(path)-1]+"/index.html"
                addIndex=True
            if self.haveLowLevel(path):
                response=forbidden
            path=os.getcwd()+"/static"+path
            if os.path.isfile(path+".gz") and canEncoding:
                path+=".gz"
                haveGz=True
            
            if os.path.isfile(path):
                if len(response)==0:
                    create_time=rfc822.formatdate(os.path.getmtime(path))
                    if not time_modif.has_key(path) or create_time!=time_modif[path]:
#                        print "READING"
                        file_size=os.path.getsize(path)
                        file_type=mimetypes.guess_type(path, strict=True)
#                        print file_type
                        file=open(path,'r')
                        file_text=file.read()
                        file.close()
                        response+="HTTP/1.1 200 OK\r\n"
                        response+="Server: myserver/0.0.1\r\n"
                        response+="Date: "+str(date)+"\r\n"
                        response+="Content-Type: "+ str(file_type[0]) + "\r\n"
                        response+="Content-Length: " + str(file_size) + "\r\n"
#                        response+="Content-Length: "+str(len("Some text"))+"\n"
                        if haveGz:
                            response+="Content-Encoding: gzip\r\n"
                        response+="Last-Modified: "+create_time+"\r\n"
                        response+="Connection: close\r\n"
                        response+="\r\n"
                        response+=file_text
#                        response+="Some text"
                        time_modif[path]=create_time
                        cached_files[path]=response
                    else:
                        if lm==create_time:
#                            print "Not modified"
                            response=not_modified
                        else:
#                            print "From cache"
                            response=cached_files[path]
            else:
                if addIndex:
                    response=forbidden
                else:
                    response=no_file
            try:
                connection.send(response)
            except Exception, error:
#                haveGz=haveGz
                print "error"
            connection.close()
#            print "Close"

sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_address=('localhost',80)
#sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(server_address)
sock.listen(1000)

for f in range(MAX_THREADS):
    t=workThread()
    t.start()




# welinux.ru/post/5055