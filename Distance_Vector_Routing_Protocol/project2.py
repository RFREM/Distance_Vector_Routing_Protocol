#starting at line 466

def handleStep(json):
    newRT = [[0 for i in range(len(serverList) + numDisableServers)] for j in range(len(serverList) + numDisabledServers)]
    arr = json.getJSONArray("rt")
    for i in range(len(arr)):
        innerArr = arr.get(i)
        for j in range(len(innerArr)):
            newRT[i][j] = int(innerArr.get(j).toString())
    for i in range(len(serverList)):
        if serverList[i].id == myServerid:
            break
    serverList = updateRoutingTable(serverList, newRT)
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
                    if server.id == my_server_id:
                        for i in range(len(top_file_routing_table)):
                            for j in range(len(top_file_routing_table)):
                                server.routing_table[i][j] = top_file_routing_table[i][j]
                        break
                self.update_routing_table(server_list, top_file_routing_table)
            elif operation == "disable":
                disable_server_id = int(received_msg["disable_server_id"])
                if disable_server_id == my_server_id:
                    print("Link to given server is closed...")
                    return
                for i in range(len(top_file_routing_table)):
                    for j in range(len(top_file_routing_table[i])):
                        if j == disable_server_id - 1:
                            continue
                        top_file_routing_table[j][disable_server_id-1] = 9999
                        top_file_routing_table[disable_server_id-1][j] = 9999 
                for server in server_list:
                    if server.id == my_server_id:
                        server.neighbors_id_and_cost.pop(disable_server_id, None)
                        for i in range(len(top_file_routing_table)):
                            for j in range(len(top_file_routing_table[i])):
                                server.routing_table[i][j] = top_file_routing_table[i][j]
                        break
                server_list.pop(disable_server_id-1)
                hashtag_next.pop(disable_server_id, None)
                num_disabled_servers += 1
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
                    if server.id == my_server_id:
                        server.neighbors_id_and_cost.pop(crash_id, None)
                        for i in range(len(top_file_routing_table)):
                            for j in range(len(top_file_routing_table[i])):
                                server.routing_table[i][j] = top_file_routing_table[i][j]
                        break
                server_list.pop(crash_id-1)
                hashtag_next.pop(crash_id, None)
                num_disabled_servers


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
