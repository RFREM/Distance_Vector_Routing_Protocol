import socket
import sys
import time
from typing import List, Dict
import threading
import json


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
        self.myServerId = 0 # The ID of this server
        #B&R: Changed my_server_id to myServerId
        self.my_port = 0 # The port of this server
        self.hashtag_next = {} # Dictionary for holding the next hop information
        self.my_ip = "" # The IP address of this server
        self.server_socket = None # The socket for this server
        self.numDisabledServers = 0 # The number of disabled servers
        #B&R: RENAMED FROM numDisabledServers to numDisabledServers
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
                self.top_file_routing_table = [[0 for i in range(len(self.server_list) + self.numDisabledServers)] for j in range(len(self.server_list) + self.numDisabledServers)]

                for i in range(len(self.server_list)):
                    if self.server_list[i].id == self.myServerId:
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
                elif server_2 == self.myServerId:
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
                if int(command_split[1]) == self.myServerId:
                    print("You cannot disable yourself")
                    continue

                self.send_disable_to_server_list(int(command_split[1]))
                self.numDisabledServers += 1
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
                            self.myServerId = int(command_split[0])
                            # add the neighbor ID and cost to a dictionary
                            new_neighbor_id_and_cost[int(command_split[1])] = int(command_split[2])
                            # Set the hashtag_next dictionary
                            self.hashtag_next[int(command_split[1])] = int(command_split[1])
                    else:
                        raise Exception("Topology File Not Correctly Formatted!")

                # Find the server in the server list 
                for i in range(len(server_list)):
                    # if it matches with this server's ID
                    if server_list[i].id == self.myServerId:
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
                print(e)

        # For each server in the server_list
        for i in range(len(server_list)):
            # If the server is the current server
            if server_list[i].get_id() == self.myServerId:
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
            if server_list[i].id == self.myServerId:
                # Loop over each possible destination server
                for j in range(len(server_list)+self.numDisabledServers+1):
                    # If we have a next hop for this destination
                    if self.hashtag_next.__contains__(j):
                        # Print out the destination ID, the next hop for this destination, and the cost of the path
                        print("    " + str(j) + "\t   " + str(self.hashtag_next.get(j)) + "\t      " + str(server_list[i].routing_table[self.myServerId-1][j-1]))
                # Exit the loop over servers
                break
    
    # This fucntion updates the link cost between two servers, then send this update to all other servers
    def update_link_cost_and_send(self, server_1, server_2, new_cost):
        # If the new cost is infinite
        if new_cost == "inf".casefold():
            # the cost in the table is set to 9999
            self.top_file_routing_table[server_1-1][server_2-1] = 9999
        else:
            # it's set to the integer value of the new cost
            self.top_file_routing_table[server_1-1][server_2-1] = int(new_cost)

        # updates the routing table of the current server based on the updated link cost 
        # It loops through the routing table and updates each value with the corresponding value in the top_file_routing_table
        for x in range(len(self.server_list)):
            if self.server_list[x].id == self.myServerId:
                for i in range(len(self.top_file_routing_table)):
                    for j in range(len(self.top_file_routing_table[i])):
                        self.server_list[x].routing_table[i][j] = self.top_file_routing_table[i][j]
                break
        
        json_dict = {}
        # creates a dictionary(json) store the update operation
        try:
            json_dict["operation"] = "update"
            json_dict["update_server_id_1"] = server_1
            json_dict["update_server_id_2"] = server_2
            json_dict["cost"] = new_cost
            json_dict["sender_id"] = self.myServerId

        except Exception as e:
            print("Connection failed...")
            print(e)
        
        # Send the update message to all the other servers in the network
        try:
            for i in range(len(self.server_list)):
                ip = socket.gethostbyname(self.server_list[i].ip_address)
                s = socket.socket()
                s.connect((ip, self.server_list[i].port))
                s.sendall(json.dumps(json_dict).encode())
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
            if self.server_list[x].id == self.myServerId:
                self.server_list[x].neighbors_id_and_cost.pop(dsid, None)
                for i in range(len(self.top_file_routing_table)):
                    for j in range(len(self.top_file_routing_table[i])):
                        self.server_list[x].routing_table[i][j] = self.top_file_routing_table[i][j]
                break
        
        json_dict = {}
        try:
            # creates a dictionary(json) store disable operation
            json_dict["operation"] = "disable"
            json_dict["disable_server_id"] = dsid

        except Exception as e:
            print("Connection failed...")
            print(e)

        # Send the disable message to all the other servers in the network
        try:
            for i in range(len(self.server_list)):
                if self.server_list[i].id == self.myServerId:
                    continue
                ip = socket.gethostbyname(self.server_list[i].ip_address)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((ip, self.server_list[i].port))
                s.sendall(json.dumps(json_dict).encode())
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

    ###########################################SECOND HALF##################################################
    def handleStep(self, json):
        #B&R: passing self into function for numdisabled erver, updaterouting, and myserverid
        newRT = [[0 for i in range(len(serverList) + self.numDisabledServers)] for j in range(len(serverList) + self.numDisabledServers)]
        arr = json.getJSONArray("rt")
        for i in range(len(arr)):
            innerArr = arr.get(i)
            for j in range(len(innerArr)):
                newRT[i][j] = int(innerArr.get(j).toString())
        for i in range(len(serverList)):
            if serverList[i].id == self.myServerid:
                break
        serverList = self.updateRoutingTable(serverList, newRT)
        return

    def SendCrash():
        infoObj = {
            "operation": "crash",
            "server_id": myserverId
        }

        try:
            for server in serverList:
                if server.id == myserverId:
                    continue
                ip = socket.gethostbyname(server.ipAddress)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, server.port))
                    s.sendall(json.dumps(infoObj).encode())
        except:
            print("Connection failed...")

    def sendRoutingTableToNeighbor(ipAddressOfNeighbor, portOfNeighbor):
        json_dict = {}
        try:
            json_dict["operation"] = "step"
            json_dict["sender_id"] = myserverId
            for i in range(len(serverList)):
                if serverList[i].id == myserverId:
                    json_dict["rt"] = serverList[i].routingTable
                    break
    
        except Exception as e:
            print("JSON Object Error")
            print(e)

        try:
            ip = socket.gethostbyname(ipAddressOfNeighbor)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, portOfNeighbor))
            s.sendall(json.dumps(json_dict).encode())
            s.close()
        
        except Exception as e:
            print("Connection failed...")
            print(e)

        def createRoutingTable(serverList):
            for i in range(len(serverList)):
                serverList[i].routingTable = [[9999 for j in range(len(serverList)+numDisabledServers)] for k in range(len(serverList)+numDisabledServers)]
                if serverList[i].id == myserverId:
                    for j in range(len(serverList[i].routingTable)):
                        if j == myserverId - 1:
                            serverList[i].routingTable[j][j] = 0
                        else:
                            serverList[i].routingTable[j][j] = 9999
                else:
                    for j in range(len(serverList[i].routingTable)):
                        serverList[i].routingTable[j][j] = 9999

            # iterate through id and costs of neighboring servers to assign their respective link costs to current server
            for i in range(len(serverList)):
                if serverList[i].id == myserverId:
                    for j in range(len(serverList[i].routingTable)):
                        if j + 1 == myserverId:
                            for key, value in serverList[i].neighborsIdAndCost.items():
                                serverList[i].routingTable[j][key - 1] = value
                            break
                    break
            return serverList

    class Connection:
        def __init__(self, socket):
            self.clientSocket = socket

        # read messages from other servers
        def run(self):
            while True:
                line = self.clientSocket.recv(1024).decode()
                if not line:
                    return
                receivedMSG = json.loads(line)
                operation = receivedMSG.get("operation")
                sender_id = receivedMSG.get("sender_id")
                if operation == "step":
                    print("Received a message from server", sender_id)
                    self.handleStep(receivedMSG)
                elif operation == "update":
                    print("Received a message from server", sender_id)
                    newCost = receivedMSG.get("cost")
                    update_server_id_1 = int(receivedMSG.get("update_server_id_1"))
                    update_server_id_2 = int(receivedMSG.get("update_server_id_2"))
    
                    if newCost == "inf":
                        self.topFileRoutingTable[update_server_id_2-1][update_server_id_1-1] = 9999
                    else:
                        self.topFileRoutingTable[update_server_id_2-1][update_server_id_1-1] = int(newCost)
                    for x in range(len(self.serverList)):
                        if self.serverList[x].id == self.myServerId:
                            for i in range(len(self.topFileRoutingTable)):
                                for j in range(len(self.topFileRoutingTable[i])):
                                    self.serverList[x].routingTable[i][j] = self.topFileRoutingTable[i][j]
                            break
                    self.updateRoutingTable(self.serverList, self.topFileRoutingTable)
    
                elif operation == "disable":
                    disable_server_id = int(receivedMSG.get("disable_server_id"))
                    if disable_server_id == self.myServerId:
                        print("Link to given server is closed...")
                        exit(0)
    
                    for i in range(len(self.topFileRoutingTable)):
                        for j in range(len(self.topFileRoutingTable[i])):
                            if j == (disable_server_id-1):
                                continue
                            self.topFileRoutingTable[j][disable_server_id-1] = 9999
                            self.topFileRoutingTable[disable_server_id-1][j] = 9999 
    
                    for x in range(len(self.serverList)):
                        if self.serverList[x].id == self.myServerId:
                            self.serverList[x].neighborsIdAndCost.pop(disable_server_id, None)
                            for i in range(len(self.topFileRoutingTable)):
                                for j in range(len(self.topFileRoutingTable[i])):
                                    self.serverList[x].routingTable[i][j] = self.topFileRoutingTable[i][j]
                            break

    class Connection(threading.Thread):
        def __init__(self, client_socket):
            threading.Thread.__init__(self)
            self.client_socket = client_socket

        # read messages from other servers
        def run(self):
            while True:
                line = self.client_socket.recv(1024).decode()
                if not line:
                    return

                received_msg = json.loads(line)
                operation = received_msg["operation"]
                sender_id = received_msg["sender_id"]

                if operation == "step":
                    print(f"Received a message from server {sender_id}\n")
                    self.handle_step(received_msg)

                elif operation == "update":
                    print(f"Received a message from server {sender_id}\n")
                    new_cost = received_msg["cost"]
                    server1 = int(received_msg["update_server_id_1"])
                    server2 = int(received_msg["update_server_id_2"])

                    if new_cost.lower() == "inf":
                        top_file_routing_table[server2-1][server1-1] = 9999
                    else:
                        top_file_routing_table[server2-1][server1-1] = int(new_cost)

                    for server in server_list:
                        if server.id == myServerId:
                            for i in range(len(top_file_routing_table)):
                                for j in range(len(top_file_routing_table)):
                                    server.routing_table[i][j] = top_file_routing_table[i][j]
                            break
                    self.update_routing_table(server_list, top_file_routing_table)

                elif operation == "disable":
                    disable_server_id = int(received_msg["disable_server_id"])
                    if disable_server_id == myServerId:
                        print("Link to given server is closed...")
                        return

                    for i in range(len(top_file_routing_table)):
                        for j in range(len(top_file_routing_table[i])):
                            if j == disable_server_id - 1:
                                continue
                            top_file_routing_table[j][disable_server_id-1] = 9999
                            top_file_routing_table[disable_server_id-1][j] = 9999 

                    for server in server_list:
                        if server.id == myServerId:
                            server.neighbors_id_and_cost.pop(disable_server_id, None)
                            for i in range(len(top_file_routing_table)):
                                for j in range(len(top_file_routing_table[i])):
                                    server.routing_table[i][j] = top_file_routing_table[i][j]
                            break

                    server_list.pop(disable_server_id-1)
                    hashtag_next.pop(disable_server_id, None)
                    numDisabledServers += 1
                    num_packets += 1

                elif operation == "crash":
                    crash_id = int(received_msg["server_id"])
                    print(f"Server {crash_id} has crashed. Updating routing table..")
                    for i in range(len(top_file_routing_table)):
                        for j in range(len(top_file_routing_table[i])):
                            if j == crash_id - 1:
                                continue
                            top_file_routing_table[j][crash_id-1] = 9999
                            top_file_routing_table[crash_id-1][j] = 9999

                    for server in server_list:
                        if server.id == myServerId:
                            server.neighbors_id_and_cost.pop(crash_id, None)
                            for i in range(len(top_file_routing_table)):
                                for j in range(len(top_file_routing_table[i])):
                                    server.routing_table[i][j] = top_file_routing_table[i][j]
                            break

                    server_list.pop(crash_id-1)
                    hashtag_next.pop(crash_id, None)
                    numDisabledServers

    def run():
        # create a socket and bind it to the port
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('localhost', myPort))

        # loop until a termination signal is received
        while True:
            try:
                # receive data from the socket
                data, address = sock.recvfrom(1024)

                # decode the data
                decodedData = data.decode('utf-8')

                # parse the received message as JSON
                receivedMSG = json.loads(decodedData)

                # handle different message types
                messageType = receivedMSG['type']

                if messageType == 'routing':
                    # update routing table
                    senderID = int(receivedMSG['sender_id'])
                    cost = int(receivedMSG['cost'])
                    for i in range(len(topFileRoutingTable)):
                        if i != myServerId-1:
                            if i == senderID-1:
                                topFileRoutingTable[i][senderID-1] = cost
                            else:
                                if (topFileRoutingTable[senderID-1][i] + cost) < topFileRoutingTable[myServerId-1][i]:
                                    topFileRoutingTable[myServerId-1][i] = topFileRoutingTable[senderID-1][i] + cost
                    # increment the number of received packets
                    numPackets += 1

                else:
                    if messageType == 'disable':
                        # disable server
                        disable_serevr_id = int(receivedMSG['server_id'])
                        serverList.pop(disable_serevr_id-1)
                        hashtagNext.pop(disable_serevr_id)
                        numDisabledServers += 1
                        numPackets += 1
                    elif messageType == 'crash':
                        # handle server crash
                        crashId = int(receivedMSG['server_id'])
                        print('Server', crashId, 'has crashed. Updating routing table..')
                        for i in range(len(topFileRoutingTable)):
                            if i == crashId-1:
                                continue
                            topFileRoutingTable[i][crashId-1] = 9999
                            topFileRoutingTable[crashId-1][i] = 9999
                        for server in serverList:
                            if server.id == myServerId:
                                server.neighborsIdAndCost.pop(crashId)
                                for i in range(len(topFileRoutingTable)):
                                    for j in range(len(topFileRoutingTable[i])):
                                        server.routingTable[i][j] = topFileRoutingTable[i][j]
                                break
                        serverList.pop(crashId-1)
                        hashtagNext.pop(crashId)
                        numDisabledServers += 1
                        numPackets += 1
            except socket.error:
                print('Connection to a server has failed')

    def step(serverList):
        for server in serverList:
            if server.id == myServerId:
                for neighbor, cost in server.neighborsIdAndCost.items():
                    ipAddressOfNeighbor = ""
                    portOfNeighbor = 0
                    for s in serverList:
                        if s.id == neighbor:
                            ipAddressOfNeighbor = s.ipAddress
                            portOfNeighbor = s.port
                            break
                    try:
                        sendRoutingTableToNeighbor(ipAddressOfNeighbor, portOfNeighbor)
                    except:
                        pass
                break
    def updateRoutingTable(serverList, nrt):
        myOriginalRoutingTable = [[0 for i in range(len(serverList) + numDisabledServers)] for j in range(len(serverList) + numDisabledServers)]
        myNewRoutingTable = [[0 for i in range(len(serverList) + numDisabledServers)] for j in range(len(serverList) + numDisabledServers)]

        i = 0
        for i in range(len(serverList)):
            if serverList[i].getId() == myServerId:
                for j in range(len(serverList[i].routingTable)):
                    for k in range(len(serverList[i].routingTable[j])):
                        itr = iter(serverList[i].neighborsIdAndCost.items())
                        neighbors = [0 for l in range(len(serverList[i].neighborsIdAndCost))]
                        x = 0
                        while itr:
                            try:
                                entry = next(itr)
                                neighbors[x] = entry[0]
                                x += 1
                            except StopIteration:
                                break

                        for j in range(len(myNewRoutingTable)):
                            for k in range(len(myNewRoutingTable[j])):
                                if j == k:
                                    pass
                                else:
                                    if myNewRoutingTable[j][k] < nrt[j][k]:
                                        pass
                                    else:
                                        myNewRoutingTable[j][k] = nrt[j][k]

                        for j in range(len(myNewRoutingTable)):
                            if j + 1 == myServerId:
                                hop = 0
                                for k in range(len(myNewRoutingTable[j])):
                                    hop += 1
                                    if j == k:
                                        pass
                                    else:
                                        newCosts = [0 for a in range(len(serverList[i].neighborsIdAndCost))]
                                        for a in range(len(neighbors)):
                                            newCosts[a] = myNewRoutingTable[j][neighbors[a] - 1] + myNewRoutingTable[neighbors[a] - 1][k]

                                        minCost = 9999
                                        for a in range(len(newCosts)):
                                            if minCost > newCosts[a]:
                                                minCost = newCosts[a]
                                                hashtagNext[hop] = neighbors[a]

                                        myNewRoutingTable[j][k] = minCost

                        didRoutingTableChange = False
                        for s in range(len(serverList[i].routingTable)):
                            for t in range(len(serverList[i].routingTable[s])):
                                if myNewRoutingTable[s][t] != myOriginalRoutingTable[s][t]:
                                    didRoutingTableChange = True
                                    break

                        if didRoutingTableChange:
                            serverList[i].routingTable = myNewRoutingTable

                        return serverList

        class ScheduledTask(TimerTask):
            def run():
                print("Routing update has been sent..\n")
                step(serverList)

        return serverList