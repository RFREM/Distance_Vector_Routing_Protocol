import socket
import sys
import time
from typing import List, Dict
import threading
import json

# video doesn't show the ServerInfo class, just making assumptions
class ServerInfo:
    def __init__(self):
        self.id = None
        self.ip_address = None
        self.port = None
        self.neighbors_id_and_cost = None
        self.no_of_packets_received = None
        self.routing_table = None
    
    def set_id(self, id):
        self.id = id
    
    def get_id(self):
        return self.id
        
    def set_ip_address(self, ip):
        self.ip_address = ip
    
    def get_ip_address(self):
        return self.ip_address

    def set_port(self, port):
        self.port = port
    
    def get_port(self):
        return self.port

    def set_neighbors_id_and_cost(self, neighbors_id_and_cost):
        self.neighbors_id_and_cost = neighbors_id_and_cost
    
    def get_neighbors_id_and_cost(self):
        return self.neighbors_id_and_cost

    def set_no_of_packets_received(self, no_of_packets_received):
        self.no_of_packets_received = no_of_packets_received
    
    def get_no_of_packets_received(self):
        return self.no_of_packets_received

    def set_routing_table(self, routing_table):
        self.routing_table = routing_table

    def get_routing_table(self):
        return self.routing_table

        
class DistanceVectorRouting:
    def __init__(self):
        self.server_list = [] # A list of ServerInfo objects
        self.top_file_routing_table = [] # 2D list for holding the routing table read from topology file
        self.update_interval = 1000 # The interval in milliseconds between updates to routing table
        self.my_server_id = 0 # The ID of this server
        self.my_port = 0 # The port of this server
        self.hashtag_next = {} # Dictionary for holding the next hop information
        self.my_ip = "" # The IP address of this server
        self.server_socket = None # The socket for this server
        self.num_disabled_servers = 0 # The number of disabled servers
        self.num_packets = 0 # The number of packets received by this server
    
    def start_up(self):
        while True:
            line = input(">>").strip() # Get input from user
            command_split = line.split(" ") # Split the input into a list of strings

            if len(command_split) < 1:
                print("Incorrect Command") # If input is empty, print error message
                continue

            command = command_split[0] # Get the first string in the list as the command

            # If the command is "server", set up the server and routing table 
            # from the topology file and start the update timer
            if command == "server": 
                try:
                    self.update_interval = int(command_split[4]) # Set the update interval
                except:
                    print("Server Command Incorrect") # Print error message if command is incorrect
                    continue
                
                # Read the topology file and set up the routing table
                self.server_list = self.read_top_file(command_split[2], self.server_list)
                self.server_list = self.create_routing_table(self.server_list)

                self.update_interval = self.update_interval * 1000
                
                # Java code:
                # Timer timer = new Timer();
                # ScheduledTask st = new ScheduledTask();
                # timer.schedule(st, updateInterval, updateInterval);

                # Convert the update interval to milliseconds and start the update timer
                # not sure ? how to convert this part to python
                timer = threading.Timer()
                st = ScheduledTask()
                timer.schedule(st, self.update_interval, self.update_interval)

                # Set up the top_file_routing_table
                self.top_file_routing_table = [[0 for i in range(len(self.server_list) + self.num_disabled_servers)] for j in range(len(self.server_list) + self.num_disabled_servers)]

                for i in range(len(self.server_list)):
                    if self.server_list[i].id == self.my_server_id:
                        for s in range(len(self.server_list[i].routing_table)):
                            for t in range(len(self.server_list[i].routing_table[s])):
                                self.top_file_routing_table[s][t] = self.server_list[i].routing_table[s][t]
                        break

                print(f"{command} SUCCESS\n")

            # If the command is "help", print the list of supported commands
            elif command == "help":
                print(f"{line} SUCCESS")
                print("\nList of Commands supported:\n"
                    ">> help\n"
                    ">> update <server id 1> <server id 2> <link cost>\n"
                    ">> step\n"
                    ">> packets\n"
                    ">> displayp\n"
                    ">> disable <server id>\n"
                    ">> crash\n")
            
            # If the command is "update", update the link cost and send it to the other server
            elif command == "update":
                server_1 = int(command_split[1])
                server_2 = int(command_split[2])
                new_cost = command_split[3]

                if server_1 == server_2:
                    print("Command entered incorrectly...")
                elif server_2 == self.my_server_id:
                    self.update_link_cost_and_send(server_2, server_1, new_cost)
                else:
                    self.update_link_cost_and_send(server_1, server_2, new_cost)

            elif command == "step":
                self.step(self.server_list)
                print("STEP SUCCESS\n")

            elif command == "packets":
                self.display_packets()
                print("PACKETS SUCCESS\n")

            elif command == "display":
                print()
                self.display_route_table(self.server_list)
                print("\nDISPLAY SUCCESS\n")

            elif command == "disable":
                if int(command_split[1]) == self.my_server_id:
                    print("You cannot disable yourself")
                    continue

                self.send_disable_to_server_list(int(command_split[1]))
                self.num_disabled_servers += 1
                print("\nDISPLAY SUCCESS\n")
            
            elif command == "crash":
                self.send_crash()
                print("SERVER CRASH SUCCESS. SHUTTING DOWN...")
                sys.exit(1)

    # This function reads a topology file which contains information about the servers in the network and their connections
    def read_top_file(self, file_name, server_list):
        total_servers_count = 0 
        num_neighbors = 0
        new_neighbor_id_and_cost = {}

        try:
            # open the topology file
            with open(file_name, 'r') as my_reader:
                # Read the first line of the topology file
                line = my_reader.readline()
                if line:
                    # set the total number of servers
                    total_servers_count = int(line.strip())
                else:
                    # Raise an exception if the file is not formatted correctly
                    raise Exception("Topology File Not Correctly Formatted!")
                
                # Read the second line of the topology file
                line = my_reader.readline()
                if line:
                    # set the total number of neighbors for this server
                    num_neighbors = int(line.strip())
                else:
                    raise Exception("Topology File Not Correctly Formatted!")

                # Loop through the server list and add the server information to the list
                for i in range(total_servers_count):
                    line = my_reader.readline()
                    if line:
                        command_split = line.split(" ")
                        if len(command_split) != 3:
                            raise Exception("Topology File Not Correctly Formatted!")
                        else:
                            new_serv = ServerInfo() # create new server object
                            new_serv.set_id(int(command_split[0])) # set server ID
                            new_serv.set_ip_address(command_split[1]) # set server IP address
                            new_serv.set_port(command_split[2]) # set server port
                            new_serv.set_no_of_packets_received(0) # initialize number of packets received to 0
                            server_list.append(new_serv) # add new server object to server list
                    else:
                        raise Exception("Topology File Not Correctly Formatted!")
                    
                # Loop through neighbors and add them to the list of neighbors for this server
                for i in range(num_neighbors):
                    line = my_reader.readline()
                    if line:
                        command_split = line.split(" ")
                        if len(command_split) != 3:
                            raise Exception("Topology File Not Correctly Formatted!")
                        else:
                            # set my server ID to first item in line
                            self.my_server_id = int(command_split[0])
                            # add the neighbor ID and cost to a dictionary
                            new_neighbor_id_and_cost[int(command_split[1])] = int(command_split[2])
                            # Set the hashtag_next dictionary
                            self.hashtag_next[int(command_split[1])] = int(command_split[1])
                    else:
                        raise Exception("Topology File Not Correctly Formatted!")

                # Find the server in the server list 
                for i in range(len(server_list)):
                    # if it matches with this server's ID
                    if server_list[i].id == self.my_server_id:
                        # set its IP address and port
                        self.my_port = server_list[i].port
                        break
                
                # Get this server's IP address and create a server socket
                self.my_ip = socket.gethostbyname(socket.gethostname())
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.bind((self.my_ip, self.my_port))
                # Call the bootup function
                self.bootup()

        except Exception as e:
                print(str(e))

        # For each server in the server_list
        for i in range(len(server_list)):
            # If the server is the current server
            if server_list[i].get_id() == self.my_server_id:
                # Set the neighbors of this server with the new neighbor information
                server_list[i].set_neighbors_id_and_cost(new_neighbor_id_and_cost)
            else:
                # Otherwise, set the neighbors of this server to an empty hash map
                empty_hash_map = {}
                empty_hash_map[0] = 0
                server_list[i].set_neighbors_id_and_cost(empty_hash_map)
        
        # Return the updated server list
        return server_list

    # This function prints out a routing table for the server
    def display_route_table(self, server_list):
         # Print a heading for the routing table
        print("\nRouting Table is: ")
        print("\n(ID) (Next Hop) (Cost)")
        
        # Loop over each server in the server list
        for i in range(len(server_list)):
            # If this is the current server
            if server_list[i].id == self.my_server_id:
                # Loop over each possible destination server
                for j in range(server_list.size()+self.num_disabled_servers+1):
                    # If we have a next hop for this destination
                    if self.hashtag_next.__contains__(j):
                        # Print out the destination ID, the next hop for this destination, and the cost of the path
                        print("    " + str(j) + "\t   " + str(self.hashtag_next.get(j)) + "\t      " + str(server_list[i].routing_table[self.my_server_id-1][j-1]))
                # Exit the loop over servers
                break
    
    # This fucntion updates the link cost between two servers, then send this update to all other servers
    def update_link_cost_and_send(self, server_1, server_2, new_cost):
        # If the new cost is infinite
        if new_cost.lower() == "inf":
            # the cost in the table is set to 9999
            self.top_file_routing_table[server_1-1][server_2-1] = 9999
        else:
            # it's set to the integer value of the new cost
            self.top_file_routing_table[server_1-1][server_2-1] = int(new_cost)

        # updates the routing table of the current server based on the updated link cost 
        # It loops through the routing table and updates each value with the corresponding value in the top_file_routing_table
        for x in range(len(self.server_list)):
            if self.server_list[x].id == self.my_server_id:
                for i in range(len(self.top_file_routing_table)):
                    for j in range(len(self.top_file_routing_table[i])):
                        self.server_list[x].routing_table[i][j] = self.top_file_routing_table[i][j]
                break
        
        # creates a dictionary containing information about the update operation
        infoObj = {
            "operation": "update",
            "update_server_id_1": server_1,
            "update_server_id_2": server_2,
            "cost": new_cost,
            "sender_id": self.my_server_id
        }
        
        # Send the update message to all the other servers in the network
        try:
            for i in range(len(self.server_list)):
                ip = socket.gethostbyname(self.server_list[i].ip_address)
                s = socket.socket()
                s.connect((ip, self.server_list[i].port))
                dataOutputStream = s.makefile(mode='wb')
                dataInputStream = s.makefile(mode='rb')
                dataOutputStream.write(str(infoObj))
        except Exception as e:
            print("Connection failed...")
        
        # update the routing table 
        self.update_routing_table(self.server_list, self.top_file_routing_table)
        # Call the step function to trigger the next iteration of the algorithm
        self.step(self.server_list)

    def send_disable_to_server_list(self, dsid):
        # Iterate over the entire routing table and update the entries where the disabled server is involved
        for i in range(len(self.top_file_routing_table)):
            for j in range(len(self.top_file_routing_table[i])):
                if j == (dsid - 1):
                    continue
                self.top_file_routing_table[j][dsid-1] = 9999
                self.top_file_routing_table[dsid-1][j] = 9999

        # Update the routing table and remove the disabled server from the neighbor's list        
        for x in range(len(self.server_list)):
            if self.server_list[x].id == self.my_server_id:
                self.server_list[x].neighbors_id_and_cost.pop(dsid, None)
                for i in range(len(self.top_file_routing_table)):
                    for j in range(len(self.top_file_routing_table[i])):
                        self.server_list[x].routing_table[i][j] = self.top_file_routing_table[i][j]
                break
        
        # creates a dictionary containing information about the disable operation
        infoObj = {
            "operation": "disable",
            "disable_server_id": dsid
        }

        # Send the disable message to all the other servers in the network
        try:
            for i in range(len(self.server_list)):
                if self.server_list[i].id == self.my_server_id:
                    continue
                ip = socket.gethostbyname(self.server_list[i].ip_address)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((ip, self.server_list[i].port))
                dataOutputStream = s.makefile('wb')
                dataInputStream = s.makefile('rb')
                dataOutputStream.write(str(infoObj))
        except Exception as e:
            print("Connection failed...")

        # Remove the disabled server from the server list and from the hashtag_next dictionary
        self.server_list.pop(dsid-1)
        self.hashtag_next.pop(dsid, None)
        # Call the step function to trigger the next iteration of the algorithm
        self.step(self.server_list)

    # This function dsplay the packets reveived by the server   
    def display_packets(self):
        print("Number of packets received: " + str(self.num_packets) + "\n")
        self.num_packets = 0 

    # The bootup function initializes the server socket and starts a new thread to handle incoming client connections
    def bootup(self):
        def connection_handler():
            while True:
                try:
                    # create connection with server
                    client_socket = self.server_socket.accept()
                    # creates a new thread with client socket and starts it
                    threading.Thread(target=self.connection, args=(client_socket,)).start()
                except socket.error:
                    pass

        threading.Thread(target=connection_handler).start()

if __name__ == "__main__":
    DistanceVectorRouting.start_up(sys.argv)