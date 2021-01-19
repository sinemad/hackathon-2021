i#-*- coding: utf-8 -*-
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
    'Description': 'Port Rename Agent',
    'Version': '0.1',
    'Author': 'Aruba123'
}

# The Parameters defined by the administrator. We should probably allow the admin to specify individual interfaces or all interfaces
ParameterDefinitions = {
    'port_id': {
        'Name': 'Port Id',
        'Description': 'Port to be renamed',
        'Type': 'string',
        'Default': '1/1/1'                      # TODO: We need to allow the admin to either select individual interfaces or all interfaces
    }                                           #       for testing right now we will do a single interface to make troubleshooting easier.
}

class Policy(NAE):

    def __init__(self):

# Setup the Monitor to trigger when a port authentication happens
        uri1 = '/system/interfaces/{}/port_access_clients'  # The attribute we want to monitor, in this case it is port_access_clients
        self.m1 = Monitor(              # Declare our monitor
            uri1,                       # URI of the attribute we are monitoring
            'Port access Client Name',  # Name of the monitor
            [self.params['port_id']])   # Currently we are just looking at one defined interface from ParameterDefinitions above
                                        # TODO: We need to monitor all interfaces, will do that after we have one interface working
        self.r1 = Rule('Port disabled administratively')                    # TODO: Once we know the possible values of the attribure then we will need to build rules
                                                                            #       for all the possible conditions
        self.r1.condition('transition {} from "up" to "down"', [self.m1])   # TODO: Build condition based upon possible values
        self.r1.action(self.action_port_down)                               # TODO: Modify to function that will handle this condition

#Reset policy status when port is up
        self.r2 = Rule('Port enabled administratively')
        self.r2.condition('transition {} from "down" to "up"', [self.m1])   # TODO: Build condition based upon possible values
        self.r2.action(self.action_port_up)                                 # TODO: Modify to function that will handle this condition

    def action_port_down(self, event):                                      # THESE ARE PLACEHOLDERS and WILL BE CHANGED       
        ActionSyslog(
            'Port {} is disabled administratively',
            [self.params['port_id']])
        ActionCLI("show lldp configuration {}", [self.params['port_id']])
        ActionCLI("show interface {} extended", [self.params['port_id']])
        if self.get_alert_level() != AlertLevel.CRITICAL:
            self.set_alert_level(AlertLevel.CRITICAL)
        self.logger.debug("### Critical Callback executed")

    def action_port_up(self, event):                                        # THESE ARE PLACEHOLDERS and WILL BE CHANGED
        self.logger.info("Current alert level: " + str(self.get_alert_level()))
        if self.get_alert_level() is not None:
            ActionSyslog(
                'Port {} is enabled administratively',
                [self.params['port_id']])
            self.remove_alert_level()
            self.logger.debug('Unset the previous status')

        self.logger.debug('### Normal Callback executed')