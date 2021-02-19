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

Manifest = {
    'Name': 'port_rename',
    'Description': 'Rename port based on authenticated user',
    'Version': '1.0',
    'TargetSoftwareVersion': '10.04',
    'Author': 'Team Aruba123'
}

# cribbed this from the github NAE ase script - vsx_health_monitor.py
def rest_get(url):
    """
    Performs a HTTP Get operation and returns the result of
    the operation.
    :param url: URL on which the GET operation needs to be
    done
    :return: Result of the HTTP GET operation.
    """
    return get(HTTP_ADDRESS + url, verify=False, proxies={'http': None, 'https': None})



class Agent(NAE):

    def __init__(self):
        # I'm going to bring over the interface_link_state_monitor script and modify. Having to do some tricky stuff because we can only use v1 REST interface with NAE scripts :(
        # Interface status
        uri1 = '/rest/v1/system/interfaces/*?attributes=link_state' + \
            '&filter=type:system'
        self.m1 = Monitor(
            uri1,
            'Interface Link status')
        self.r1 = Rule('Link Went Down')
        self.r1.condition('transition {} from "up" to "down"', [self.m1])
        self.r1.action(self.action_interface_down)

        # Reset agent status when link is up
        self.r2 = Rule('Link Came UP')
        self.r2.condition('transition {} from "down" to "up"', [self.m1])
        self.r2.action(self.action_interface_up)

        # variables
        #self.variables['links_down'] = ''

    def action_interface_down(self, event):
        self.logger.debug("================ Down ================")
        label = event['labels']
        self.logger.debug('label: [' + label + ']')
        _, interface_id = label.split(',')[0].split('=')
        #links_down = self.variables['links_down']
        #self.logger.debug('links_down before: ['
        #                  + links_down + ']')
        #if (interface_id + ':') not in links_down:
        #    links_down = links_down + interface_id + ':'
        #    self.variables['links_down'] = links_down
        ActionSyslog('Interface ' + interface_id + ' is down')
        self.logger.debug('Interface ' + interface_id + ' is down')

        ActionCLI('show interface ' + interface_id)
        self.logger.debug('COMMAND EXECUTED: show interface ' + interface_id)

        ActionCLI('config\ninterface ' + interface_id + '\nno description \nexit\nexit')
        self.logger.debug('COMMAND EXECUTED: config interface ' + interface_id + ' no description exit exit')

        if self.get_alert_level() != AlertLevel.MINOR:
            self.set_alert_level(AlertLevel.MINOR)
        #self.logger.debug('links_down after: ['
        #                 + links_down + ']')
        self.logger.debug("================ /Down ================")

    def action_interface_up(self, event):
        self.logger.debug("================ Up ================")
        label = event['labels']
        _, interface_id = label.split(',')[0].split('=')
        self.logger.debug('Interface ' + interface_id + ' is up')
        ActionSyslog('Interface ' + interface_id + ' is up')
        uri_encoded_interface_id = interface_id.replace('/', '%2F') #"1%2F1%2F1"
        rest_uri = '/rest/v1/system/ports/' + uri_encoded_interface_id + '/port_access_clients?attributes=auth_attributes&depth=2'
        try: 
            r = rest_get(rest_uri)
            self.logger.debug("HTTP GET status: {}".format(r.status_code))
            if r.status_code != 200 :
                self.logger.debug("Check the GET status: {}".format(r.status_code))
                self.logger.debug("Check the GET status: {}".format(r.raise_for_status()))
                r.raise_for_status()
            json_results = r.json()
            auth_method = json_results[-1]['auth_attributes']
            if 'dot1x' in auth_method:
                #self.logger.debug('AUTH_METHOD: ' + str(auth_method))
                username = json_results[-1]['auth_attributes']['dot1x']['username']
                self.logger.debug('USERNAME: ' + str(username))
                ActionSyslog('User ' + username + ' logged in on port ' + interface_id)
                self.logger.debug('User ' + username + ' logged in on port ' + interface_id)

                ActionCLI('show interface ' + interface_id)
                self.logger.debug('COMMAND EXECUTED: show interface ' + interface_id)

                ActionCLI("config\ninterface " + interface_id  + "\ndescription logged in user - " + username + "\nexit\nexit")
                self.logger.debug("COMMAND EXECUTED: config interface " + interface_id  + " description logged in user - " + username + " exit exit")
        except Exception as e:
            self.logger.debug("Error while making REST call to URI " 
                              "{} : {}".format(rest_uri, e)) 
        if self.get_alert_level() is not None:
            self.remove_alert_level()
        self.logger.debug("================ /Up ================")