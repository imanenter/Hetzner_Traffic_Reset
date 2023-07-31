import requests
import json
import time
from datetime import datetime

API_KEY='YOUR API KEY'


url = "https://api.hetzner.cloud/v1/servers"
payload = {}
headers = {
  'Authorization': 'Bearer '+API_KEY
}

response = requests.request("GET", url, headers=headers, data=payload)
data=response.json()
print('geting data ...')


for server in data['servers']:
    id=server['id']
    name=server['name']
    ipv4=server['public_net']['ipv4']['ip']
    ipv4_id=server['public_net']['ipv4']['id']
    type=server['server_type']['name']
    datacenter=server['datacenter']['name']
    image=server['image']['name']
    outgoing_traffic=server['outgoing_traffic']
    included_traffic=server['included_traffic']

    

############################## calcualate data
    included_traffic=int(included_traffic or 1)
    outgoing_traffic=int(outgoing_traffic or 1)
    percent_usage=outgoing_traffic/included_traffic

############################## Take snapshot
    if (float(percent_usage)>0.8):
        print('server '+name+' has high data usage')

        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y-%H:%M:%S")

        url = "https://api.hetzner.cloud/v1/servers/"+str(id)+"/actions/create_image"

        payload = json.dumps({
        "description": name+'-'+dt_string,
        "labels": {
        "labelkey": "value"
        },
        "type": "snapshot"
        })
        print("getting snapshot ...")
        response = requests.request("POST", url, headers=headers, data=payload)
        time.sleep(150)
        snap_data=response.json()
        

        if(snap_data['action']['error']==None):
          print('#---------Success---------#')
          snap_id=snap_data['image']['id']
        else:
            print('XXxx-----Got error !-----xxXX')

        ############################## Power OFF
        url="https://api.hetzner.cloud/v1/servers/"+str(id)+"/actions/poweroff"
        print("powering off ...")

        response = requests.request("POST", url, headers=headers, data=payload)


        return_data=response.json()
        if(return_data['action']['error']==None):
          print('#---------Success---------#')
        else:
            print('XXxx-----Got error !-----xxXX')

        time.sleep(10)

        ############################## Unassign IP
        url = "https://api.hetzner.cloud/v1/primary_ips/"+str(ipv4_id)+"/actions/unassign"
        print("Unassign IP ...")

        response = requests.request("POST", url, headers=headers, data=payload)

        return_data=response.json()
        if(return_data['action']['error']==None):
          print('#---------Success---------#')
        else:
            print('XXxx-----Got error !-----xxXX')

        time.sleep(10)


        ############################## Delete server
        url='https://api.hetzner.cloud/v1/servers/'+str(id)
        print("Deleting server ...")
        

        response = requests.request("DELETE", url, headers=headers, data=payload)


        return_data=response.json()
        if(return_data['action']['error']==None):
          print('#---------Success---------#')
        else:
            print('XXxx-----Got error !-----xxXX')

        time.sleep(10)

        ############################## Create new server
        url = "https://api.hetzner.cloud/v1/servers"
        print("Creating new server ...")

        payload = json.dumps({
          "datacenter": datacenter,
          "image": "ubuntu-20.04",
          "name": name,
          "public_net": {
            "enable_ipv4": True,
            "enable_ipv6": False,
            "ipv4": ipv4_id
          },
          "server_type": type,
          "start_after_create": True
        })

        response = requests.request("POST", url, headers=headers, data=payload)
        
        server_new=response.json()
        if(server_new['action']['error']==None):
          server_new_id=server_new['server']['id']
          print('#---------Success---------#')
        else:
            print('XXxx-----Got error !-----xxXX')


        
        time.sleep(60)


        ############################## Rebuild server with snapshot
        url = "https://api.hetzner.cloud/v1/servers/"+str(server_new_id)+"/actions/rebuild"
        print("Rebuilding server ...")

        payload = json.dumps({
          "image": str(snap_id)
        })

        response = requests.request("POST", url, headers=headers, data=payload)

        return_data=response.json()
        if(return_data['action']['error']==None):
          print('#---------Success Finished!---------#')
        else:
            print('XXxx-----Got error !-----xxXX')


    
    else:
        print('server '+name+' doesnt have high data usage')
