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

Manifest = {
    'Name': 'port_rename',
    'Description': 'Rename port based on authenticated user',
    'Version': '1.0',
    'TargetSoftwareVersion': '10.04',
    'Author': 'Aruba123'
}

# The Parameters defined by the administrator. We should probably allow the admin to specify individual interfaces or all interfaces
#ParameterDefinitions = {
#    'port_id': {
#        'Name': 'Port Id',
#        'Description': 'Port to be renamed',
#        'Type': 'string',
#        'Default': '1/1/1'                      # TODO: We need to allow the admin to either select individual interfaces or all interfaces
#    }                                           #       for testing right now we will do a single interface to make troubleshooting easier.
#}

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
        self.variables['links_down'] = ''

    def action_interface_down(self, event):
        self.logger.debug("================ Down ================")
        label = event['labels']
        self.logger.debug('label: [' + label + ']')
        _, interface_id = label.split(',')[0].split('=')
        self.logger.debug('interface_id - ' + interface_id)
        links_down = self.variables['links_down']
        self.logger.debug('links_down before: ['
                          + links_down + ']')
        if (interface_id + ':') not in links_down:
            links_down = links_down + interface_id + ':'
            self.variables['links_down'] = links_down
            ActionSyslog('Interface ' + interface_id + ' Link gone down')
            ActionCLI("show lldp configuration " + interface_id)
            ActionCLI("show interface " + interface_id + " extended")
            if self.get_alert_level() != AlertLevel.CRITICAL:
                self.set_alert_level(AlertLevel.CRITICAL)
        self.logger.debug('links_down after: ['
                          + links_down + ']')
        self.logger.debug("================ /Down ================")

    def action_interface_up(self, event):
        self.logger.debug("================ Up ================")
        label = event['labels']
        self.logger.debug('label: [' + label + ']')
        _, interface_id = label.split(',')[0].split('=')
        self.logger.debug('interface_id - ' + interface_id)
        links_down = self.variables['links_down']
        self.logger.debug('links_down before: ['
                          + links_down + ']')
        if (interface_id + ':') in links_down:
            links_down = links_down.replace((interface_id + ':'), '')
            self.variables['links_down'] = links_down
            self.logger.debug('links_down after: ['
                              + links_down + ']')
            ActionSyslog('Interface ' + interface_id + ' Link came up')
            if not links_down:
                if self.get_alert_level() is not None:
                    self.remove_alert_level()
        self.logger.debug("================ /Up ================")