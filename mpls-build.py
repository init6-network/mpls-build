#!/usr/bin/env python3

#list of modules to import
import json
from napalm.base import get_network_driver

#"global" variables
hostname='192.168.1.135'
defaultusername='daren'
defaultpassword='Amnes!a1'
defaultsecret='Amnes!a1'
workingpath='c:\\users\\daren\\OneDrive\\Documents\\GitHub\\mpls-build\\'
nodefilename='EVE MPLS build workbook - Nodes.csv'
optargs={'secret':defaultsecret}

#Original pseudocode

#Open node file
#Lift nodes into list of dictionaries
#Loop through node list
#  Connect to node
#  Collect interface list
#  Loop through interfaces
#    Modify description to "Test"
#    write it back

#Function to open a CSV and read it into a list of dictionaries representing record details
def readcsvfile(csvfilename):

    #initialise temp variables
    newrecord={}
    recordlist=[]

    try:
        #open the CSV file
        csvfile=open(csvfilename,"r")
    except:
        print("Cannot open file",csvfilename)
    else:
        #extract the field headings from the first line
        fieldlist=csvfile.readline().strip('\n').split(',')

        #loop through the rest of the CSV file 
        for line in csvfile:
            values=line.strip('\n').split(',')
            index=0

            #if line not commented out ...
            if values[0][0]!='#':
            #create a dictionary with the fields from the file headings
                for field in fieldlist:
                    newrecord[field]=values[index]
                    index+=1
    
                #add the dictionary to the list of dictionaries
                recordlist.append(newrecord)
                newrecord={}
        csvfile.close()

    return recordlist

#function to push config stanza to a network node, returns True if successful, False if not
def pushconfig(os,nodeaddress,username,password,secret,configtobepushed):

    #initialise deployed flag
    deployed=False

    #initialise NAPALM for IOS devices
    driver=get_network_driver(os)

    #try to push that config to switch
    try:
        #connect to node over OOB connection
        optargs={'secret':secret}
        device=driver(hostname=nodeaddress,username=username,password=password,optional_args=optargs)
        device.open()
    #if it fails
    except:
        print("*ERROR* cannot connect to",nodeaddress)
    #but we're hoping it's successful ...
    else:
        try:
            #create candidate configuration from temporary file created above
            device.load_merge_candidate(config=configtobepushed) #filename=tempfilename)
        #if there's a problem with the config creation
        except:
            print('*ERROR* problem with candidate config')
        #but hopefully all is well and config can be committed
        else:
            #attempt commit
            try:
                print("Committing "+nodeaddress)
                device.commit_config()
                deployed=True
            #discard if failed
            except:
                print("Commit failed, discarding ...")
                device.discard_config()
            #whichever way, close the device
            finally:
                device.close()

    return deployed

#function to push Loopback0 config to devices in nodelist - returns a list of nodes where changes have been deployed
def deployloopbacks(nodelist):

    #initialise list of nodes successfully deployed
    deployed=[]

    #loop through node list
    for node in nodelist:
        #assemble CLI commands
        configtobepushed="interface loopback0\nip address "+node['Loopback0']+" 255.255.255.255"

        #fetch credentials
        uname=node['username'] if (node['username']!="*default*") else defaultusername
        pword=node['password'] if (node['password']!="*default*") else defaultpassword
        sec=node['secret'] if (node['secret']!="*default*") else defaultsecret
                   
        try:
            if pushconfig(node['OS'],node['OOB address'],uname,pword,sec,configtobepushed)==True:
                print("Successful deployment to",node['Hostname'])
                deployed.append(node)
        except:
            print("*ERROR* Config failed to be pushed to",node['Hostname'])

    return deployed


#code to be run when file executed as a script
def main():
    #fetch list of network nodes from the Node CSV
    ournodes=readcsvfile(workingpath+nodefilename)

    #If there are any nodes to process ...
    if len(ournodes) > 0:
        deployednodes=deployloopbacks(ournodes)

        #initialise NAPALM for IOS devices
        driver=get_network_driver('ios')
        
        #loop through the list of nodes which successfully deployed
        for node in deployednodes:
            try:
                #connect to the node over the OOB connection
                uname=node['username'] if (node['username']!="*default*") else defaultusername
                pword=node['password'] if (node['password']!="*default*") else defaultpassword
                sec=node['secret'] if (node['secret']!="*default*") else defaultsecret
                device=driver(hostname=node['OOB address'],username=uname,password=pword,optional_args={'secret':sec})
                device.open()
            except:
                print("Cannot connect to",node['Hostname'])
            else:
                #pull the list of configured IP interfaces
                ints=device.get_interfaces_ip()
                device.close()

                #and pretty print them
                print(node['Hostname'])
                print(json.dumps(ints, sort_keys=True, indent=4))

if __name__ == "__main__":
    main()