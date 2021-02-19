#-*- coding: utf-8 -*-
#
#Copyright (c) 2017 Hewlett Packard Enterprise Development LP
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing,
#software distributed under the License is distributed on an
#"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#KIND, either express or implied. See the License for the
#specific language governing permissions and limitations
#under the License.

from requests import get

"""
NAME:           port_dot1x_user_label.py
AUTHORS:        Team Aruba123 (Jeremy Bradrick, Dan Gullick, Greg Kamer, Dan Sinema)
                File location: https://github.com/sinemad/hackathon-2021
CREDITS:        Aruba Networks github NAE ASE scripts (https://github.com/aruba/nae-scripts/blob/master/common/ase/)
                were used as example and code was derived from the following scripts: 
                1. interface_link_state_monitor.1.0.py
                    -   Basic structure used to build this script
                    -   Rule and conditions used as they were the same rule and condition
                        we needed for this script
                    -   Basic callback action functions (basically names as structure was 
                        changed significantly)
                2. vsx_health_monitor.py (rest_get() function)
                    -   Used the rest_get() functions to make the REST query we needed
                3. configuration_change_email.1.1.py ()
                    -   Used as example on how to process and handle return from rest_get()
                        function
VERSION:        1.0
STATUS:         Active
DESCRIPTION:    This script monitors the up and down state of the ports of a switch. When a interface 
                moves from up to down or down to up, a condition is triggered to discover if the 
                device is authenticated via 802.1x. If the device is authenticated via 802.1x the
                script will then update the interface's description with the 802.1x username. When the
                user disconnects the interface's description is reset. Below is example debug output of
                a user "rpi" authenticating on interface 1/1/1:
                |LOG_DEBUG|================ Up ================
                |LOG_DEBUG|Interface 1/1/1 is up
                |LOG_DEBUG|HTTP GET status: 200
                |LOG_DEBUG|USERNAME: rpi
                |LOG_DEBUG|User rpi logged in on port 1/1/1
                |LOG_DEBUG|COMMAND EXECUTED: config interface 1/1/1 description logged in user - rpi exit exit
                |LOG_DEBUG|COMMAND EXECUTED: show interface 1/1/1
                |LOG_DEBUG|================ Up ================

                Example of the user disconnecting from the interface:
                |LOG_DEBUG|================ Down ================
                |LOG_DEBUG|Interface 1/1/1 is down
                |LOG_DEBUG|COMMAND EXECUTED: config interface 1/1/1 no description exit exit
                |LOG_DEBUG|COMMAND EXECUTED: show interface 1/1/1
                |LOG_DEBUG|================ Down ================

CAVEATS:        1.  The script currently only labels interfaces if the connection is authenticated via
                    802.1x
                2.  Because with NAE scripts we can currently only use the v1 REST interface, we can
                    only trigger on the interface up/down state. If v10.04+ is ever supported there 
                    are REST interfaces that could be used to trigger on user authentication or 
                    reauthentication. 
                    (https://techhub.hpe.com/eginfolib/Aruba/OS-CX_10.04/5200-6724/index.html#GUID-09F6962C-9AD0-403C-ACE9-7814DC823F54.html)

TODO:           1. Add support for MAC AUTHENTICATION 
                    - Update description with device mac address
"""

Manifest = {
    'Name': 'port_dot1x_user_label',
    'Description': 'Rename port based on authenticated user',
    'Version': '1.0',
    'TargetSoftwareVersion': '10.04',
    'Author': 'Team Aruba123'
}

# Used the rest_get() function from github NAE ase script - vsx_health_monitor.py
def rest_get(url):
    """
    THIS FUNCTION IS FROM THE vsx_health_monitor.py; IT DID NOT MAKE SENSE TO
    RE-WRITE SINCE THE FUNCTION IS PRETTY SIMPLE.
    Performs a HTTP Get operation and returns the result of
    the operation.
    :param url: URL on which the GET operation needs to be
    done
    :return: Result of the HTTP GET operation.
    """
    return get(HTTP_ADDRESS + url, verify=False, proxies={'http': None, 'https': None})



class Agent(NAE):

    def __init__(self): #[ILSM-1.0.py]
        """
        __init__ function:
        WE USED THE BASIC STRUCTURE OF THE SCRIPT interface_link_state_monitor.1.0.py,
        MADE SIGNIFICANT CHANGES TO THE SCRIPT. THE __INIT__ IS BASICALLY THE SAME
        AS THE ORGINAL SCRIPT, BECAUSE WE ARE BASICALLY MONITORING AND TRIGGERING
        ON THE SAME ITEMS THAT interface_link_state_monitor.1.0.py DOES. WHAT WAS USED
        FROM interface_link_state_monitor.1.0.py WILL BE LABELED WITH COMMENT
        [ILSM-1.0.py] TO THE RIGHT OF THE LINE. 

        The REST item we need to monitor, this is the interface's link state
        i.e. -> Link is up or down
        """
        uri1 = '/rest/v1/system/interfaces/*?attributes=link_state' + \
            '&filter=type:system' #[ILSM-1.0.py]
        
        # Setup monitor
        self.m1 = Monitor(
            uri1,
            'Interface Link status') #[ILSM-1.0.py]
        # Rule #1 - If the link goes down trigger the action_interface_down() function
        # below.  
        self.r1 = Rule('Link Went Down') #[ILSM-1.0.py]
        self.r1.condition('transition {} from "up" to "down"', [self.m1]) #[ILSM-1.0.py]
        self.r1.action(self.action_interface_down) #[ILSM-1.0.py]

        # Rule #2 - If the link comes up trigger the action_interface_up() function
        # below. 
        self.r2 = Rule('Link Came UP') #[ILSM-1.0.py]
        self.r2.condition('transition {} from "down" to "up"', [self.m1]) #[ILSM-1.0.py]
        self.r2.action(self.action_interface_up) #[ILSM-1.0.py]

    def action_interface_down(self, event):
        """
        action_interface_down function:
        WE USED THE BASIC STRUCTURE OF THE SCRIPT interface_link_state_monitor.1.0.py,
        MADE SIGNIFICANT CHANGES TO THE SCRIPT. WE REMOVED THE dict THAT WAS USED TO
        MONITOR DOWN LINKS (WE ARE NOT REALLY CONCERNED ABOUT THAT). MOST OF THE 
        FUNCTION FROM interface_link_state_monitor.1.0.py WAS STRIPPED OUT, WHAT WAS USED
        WILL BE LABELED WITH [ILSM-1.0.py]

        THIS FUNCTION IS TRIGGERED WHEN THE INTERFACE IS DISCONNECTED. WE FIRST DISCOVER
        THE INTERFACE, THEN WE RESET THE description LABEL ('no description'). WE ALSO
        EXECUTE A BASIC show interface <iface id> SO THAT THE ADMIN CAN CONFIRM IN THE
        NAE INTERFACE THAT description LABEL WAS PROPERLY RESET.
        """
        self.logger.debug("================ Down ================") #[ILSM-1.0.py]
        # Extract the interface that triggered
        label = event['labels'] #[ILSM-1.0.py]
        _, interface_id = label.split(',')[0].split('=') #[ILSM-1.0.py]
        # Add to the Syslog and debug log for information and troubleshooting      
        ActionSyslog('Interface ' + interface_id + ' is down')
        self.logger.debug('Interface ' + interface_id + ' is down')
        # Execute this command to reset the description 
        ActionCLI('config\ninterface ' + interface_id + '\nno description \nexit\nexit')
        self.logger.debug('COMMAND EXECUTED: config interface ' + interface_id + ' no description exit exit')
        # Set the ALERT level to Minor so that the admin know something was triggered
        if self.get_alert_level() != AlertLevel.MINOR:
            self.set_alert_level(AlertLevel.MINOR)
        self.logger.debug("================ /Down ================") #[ILSM-1.0.py]

    def action_interface_up(self, event):
        """
        action_interface_up function:
        WE USED THE BASIC STRUCTURE OF THE SCRIPT interface_link_state_monitor.1.0.py,
        MADE SIGNIFICANT CHANGES TO THE SCRIPT. WE REMOVED THE dict THAT WAS USED TO
        MONITOR DOWN LINKS (WE ARE NOT REALLY CONCERNED ABOUT THAT). MOST OF THE 
        FUNCTION FROM interface_link_state_monitor.1.0.py WAS STRIPPED OUT, WHAT WAS USED
        WILL BE LABELED WITH [ILSM-1.0.py]

        THIS FUNCTION IS TRIGGERED WHEN THE INTERFACE IS CONNECTED. WE FIRST DISCOVER
        THE INTERFACE, THEN WE MAKE A REST CALL TO port_access_clients TO EXTRACT THE
        USERNAME THAT AUTHENTICATED ON THE INTERFACE. WE THEN UPDATE THE INTERFACE 
        description LABEL WITH THE USERNAME DISCOVERED FROM THE REST CALL. THE
        description LABEL IS UPDATED IN THE FOLLOWING FORMAT:
        
        Description: authenticated user - rpi

        WE ALSO
        EXECUTE A BASIC show interface <iface id> SO THAT THE ADMIN CAN CONFIRM IN THE
        NAE INTERFACE THAT description LABEL WAS PROPERLY UPDATED.
        """
        self.logger.debug("================ Up ================") #[ILSM-1.0.py]
        label = event['labels'] #[ILSM-1.0.py]
        _, interface_id = label.split(',')[0].split('=') #[ILSM-1.0.py]
         # Add to the Syslog and debug log for information and troubleshooting  
        ActionSyslog('Interface ' + interface_id + ' is up')
        self.logger.debug('Interface ' + interface_id + ' is up')
        # The interface label needs to be formated from (example): 1/1/1 to "1%2F1%2F1"
        # If the / are not converted to UTF-8 format the GET call will error with 404 (resource not found)
        uri_encoded_interface_id = interface_id.replace('/', '%2F')
        # Build the REST URI to call to get the port_access_clients data
        rest_uri = '/rest/v1/system/ports/' + uri_encoded_interface_id + '/port_access_clients?attributes=auth_attributes&depth=2'
        # This TRY is to make the REST GET call for port_access_clients data
        try:
            # Make the GET call
            r = rest_get(rest_uri) 
            # This allows the admin to troubleshoot failed GET calls
            self.logger.debug("HTTP GET status: {}".format(r.status_code))
            # If the HTTP STATUS is anything other than 200 (Successful), the print the code 
            # so the admin can troubleshoot
            if r.status_code != 200 :
                self.logger.debug("Check the GET status: {}".format(r.status_code))
                self.logger.debug("Check the GET status: {}".format(r.raise_for_status()))
                r.raise_for_status()
            # Convert the returned results to a JSON object
            json_results = r.json()
            # Because we only handle dot1x currently, we are going to extract and test
            auth_method = json_results[-1]['auth_attributes']
            if 'dot1x' in auth_method:
                # Extract username from the JSON object
                username = json_results[-1]['auth_attributes']['dot1x']['username']
                # Print to debug log for troubleshooting
                self.logger.debug('USERNAME: ' + str(username))
                # Print to Syslog and debug log for troubleshooting
                ActionSyslog('User ' + username + ' logged in on port ' + interface_id)
                self.logger.debug('User ' + username + ' logged in on port ' + interface_id)
                # Execute this command to update the interface description with the username
                ActionCLI("config\ninterface " + interface_id  + "\ndescription authenticated user - " + username + "\nexit\nexit")
                self.logger.debug("COMMAND EXECUTED: config interface " + interface_id  + " description logged in user - " + username + " exit exit")
        except Exception as e: 
            # Throw and exception if the GET returns an error or any other HTTP status than 200
            self.logger.debug("Error while making REST call to URI " 
                              "{} : {}".format(rest_uri, e)) 
        # Reset the ALERT value to None
        if self.get_alert_level() is not None: #[ILSM-1.0.py]
            self.remove_alert_level() #[ILSM-1.0.py]
        self.logger.debug("================ /Up ================") #[ILSM-1.0.py]