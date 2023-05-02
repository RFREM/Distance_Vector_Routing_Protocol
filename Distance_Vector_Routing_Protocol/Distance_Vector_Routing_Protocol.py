import socket
import threading
import subprocess

import re

subprocess.call('start DVR_C1.py', shell=True)
subprocess.call('start DVR_C2.py', shell=True)
subprocess.call('start DVR_C3.py', shell=True)
subprocess.call('start DVR_C4.py', shell=True)

hostname=socket.gethostname()   
IPAddrGET=socket.gethostbyname(hostname) 

ServerName = (hostname)
SERVER_ADDR = (IPAddrGET, 4545)

def user_interface_display():

    print("\nDistance Vector Routing Protocols & Available Commands")
    print("\n\nExpected inputs:")

    print("\n1 - help: Displays list of commands along with brief explanation.")
    
    print("\n2 - server -t <topology-file-name> -i <routing-update-interval>:   WIP ")
    
    print("\n3 - update <server-ID1> <server-ID2> <Link Cost>:  WIP ")
    
    print("\n4 - step: Forces a routing update display for neighors. ")  
    print("\n    Note - Routing updates normally periodic")
    
    print("\n5 - list: Displays a list containing all connections involving this program.")
    
    print("\n6 - packets: Display # of distance vectors current server receieved.")
    
    print("\n7 - display: Current routing table which includes its own and neighboring")
    print("\n    node's distance vector.")

    print("\n8 - disable <server-ID>: Terminate link of a stated server ID. Displays ")
    print("\n    relevent information should the given server is classified as a neighbor.")

    print("\n9 - crash: End the connection of current server to any neigboring servers.")
    print("\n    All neigbors will display a message and process the crash accordingly.")

    print("\n8 - exit: Command will close all connections and exit the program.")


def initialize_server():

    print()

def send_message():

    print()

def establish_link(server_ID_1, server_ID_2):

    print()

def update_routing():

    print()

def display_server_packets():

    print()

def get_routing_table(list_of_connections):

    print()

def display_routing_table(list_of_connections):

    print()

def disable_server(server_id_substring, list_of_connections):

    print()

def crash_server():

    print()

if __name__ == "__main__":

    list_of_connections = {}

    #dictionary key values

    #expected variables should be: connection ID | IP Address | Port Number | Socket Object | Connection Type (server/client) PROJECT 1, NEEDS UPDATE

    #server_thread_object = threading.Thread(target = initialize_server, args = [initial_ip_address, initial_server_port, list_of_connections])

    #server_thread_object.start()

    user_interface_display()

    while True:
        
        question = "\n\nPlease input command: "
        
        user_input = ""
        
        user_input = input(question)
        
        if (re.search(r"\s", user_input)):
        
            user_input_slice = user_input.split(" ")
        
        else:
        
            user_input_slice = user_input

        if user_input == "help":

            user_interface_display()
           
        elif user_input_slice[0] == "server":

            topology_name = ()  #grab the name from file passed in
        
        elif user_input_slice[0] == "update":

            blah = ()
        
        elif user_input == "step":

            blah = ()

        elif user_input == "packets":

            blah = ()

        elif user_input == "display":

            display_routing_table(list_of_connections)

        elif user_input_slice[0] == "disable":    

            server_id_substring = user_input_slice[1]
            
            disable_server(server_id_substring, list_of_connections)

        elif user_input == "crash":
            
            crash_server()           
            
            exit()

        elif user_input == "exit":
            
            print("\nProgram will terminate.")            
            
            exit()
