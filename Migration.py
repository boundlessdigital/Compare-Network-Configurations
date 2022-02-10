import meraki
import os
import json
import pprint
import click
from jsondiff import diff

API_KEY = os.environ.get('MERAKI_DASHBOARD_API')

dashboard = meraki.DashboardAPI(API_KEY)

def ensureDeviceSettings(organization_name, saved_device_settings):

    # Gets device settings into a json
    # Compares that to existing written json of device settings

    orgs = dashboard.organizations.getOrganizations()

    organization_id = ''

    for o in range(len(orgs)):
        if orgs[o]['name'] == organization_name:
            organization_id = orgs[o]['id']

    if organization_id == '':
        print("Org not found using this API key")
        return


    devices = dashboard.organizations.getOrganizationDevices(
    organization_id, total_pages='all'
    )

    response = {}

    for d in range(len(devices)):

        serial = devices[d]['serial']
        deviceFound = 0

        if 'MR' in devices[d]['model']:

            deviceFound = 1

            try:

                response.update(dashboard.wireless.getDeviceWirelessBluetoothSettings(serial))

            except meraki.APIError as e:

                if "400" in str(e):

                    print("BLE not enabled")

                response.update(dashboard.wireless.getDeviceWirelessRadioSettings(serial))

        if 'MS' in devices[d]['model']:

            deviceFound = 1

            response.update([("ports", dashboard.switch.getDeviceSwitchPorts(serial))])
            response.update(dashboard.switch.getDeviceSwitchRoutingInterfaces(serial))
            response.update(dashboard.switch.getDeviceSwitchWarmSpare(serial))
            interfaces = dashboard.switch.getDeviceSwitchRoutingInterfaces(serial)

            for i in interfaces:
                response.update(dashboard.switch.getDeviceSwitchRoutingInterfaceDhcp(serial, interfaces[i]['interfaceId']))

        if deviceFound == 1:
            response.update(dashboard.devices.getDevice(serial))

    difference = diff(response, saved_device_settings)

    if len(difference) == 0:
        "No differences found, Migration successful"

    pprint.pprint(difference)


def saveDeviceSettings(organization_name):

    # This function saves device level settings

    # Run before migration

    # Used in conjuction with ensureDeviceSettings function

    # Because devices cannot be in two places at once


    orgs = dashboard.organizations.getOrganizations()

    organization_id = ''

    for o in range(len(orgs)):
        if orgs[o]['name'] == organization_name:
            organization_id = orgs[o]['id']

    if organization_id == '':
        print("Org not found using this API key")
        return

    devices = dashboard.organizations.getOrganizationDevices(
    organization_id, total_pages='all'
    )

    response = {}

    for d in range(len(devices)):

        serial = devices[d]['serial']
        deviceFound = 0

        if 'MR' in devices[d]['model']:

            deviceFound = 1

            try:
                response.update(dashboard.wireless.getDeviceWirelessBluetoothSettings(serial))

            except meraki.APIError as e:

                if "400" in str(e):

                    print("BLE not enabled")

                response.update(dashboard.wireless.getDeviceWirelessRadioSettings(serial))

        if 'MS' in devices[d]['model']:

            deviceFound = 1

            response.update([("ports", dashboard.switch.getDeviceSwitchPorts(serial))])
            response.update(dashboard.switch.getDeviceSwitchRoutingInterfaces(serial))
            response.update(dashboard.switch.getDeviceSwitchWarmSpare(serial))
            interfaces = dashboard.switch.getDeviceSwitchRoutingInterfaces(serial)

            for i in interfaces:
                response.update(dashboard.switch.getDeviceSwitchRoutingInterfaceDhcp(serial, interfaces[i]['interfaceId']))

        if deviceFound == 1:
            response.update(dashboard.devices.getDevice(serial))

    with open('sample3.json', 'w') as configs:
        json.dump(response, configs)



def compareNetworks(network1, network2):

    # Compare configurations for 2 networks

    orgs = dashboard.organizations.getOrganizations()

    networkid_1 = 0
    networkid_2 = 0

    same_name = 0

    # Find networks based on name

    for o in range(len(orgs)):

        try:
            networks = dashboard.organizations.getOrganizationNetworks(orgs[o]['id'])

        except meraki.APIError as a:

                if "403" in str(a):
                            print("Org license information unavailable")

        for n in range(len(networks)):

            if networks[n]['name'] == network1 and same_name == 0:
                networkid_1 = networks[n]['id']
                same_name = 1

            if networks[n]['name'] == network2:
                networkid_2 = networks[n]['id']

    if networkid_1 == 0 or networkid_2 == 0:

        print("One of the networks you have entered was not found")

    data1 = getNetworkData(networkid_1)
    data2 = getNetworkData(networkid_2)

    difference = diff(data1, data2)
    difference2 = diff(data2, data1)

    if len(difference) + len(difference2) == 0:
        print("No differences found, Migration successful")
        return

    else:

        if "organizationId" in difference.keys():
            difference.pop('organizationId')

        if 'name' in difference.keys():
            difference.pop('name')

        if 'routes' in difference.keys():
            difference.pop('routes')

        if 'url' in difference.keys():
            difference.pop('url')

            if 'vlans' in difference.keys():

                vlans = 0

                while vlans < len(difference['vlans']):

                    difference['vlans'].pop(vlans, None)

                    vlans = vlans + 1

        if "organizationId" in difference2.keys():
            difference2.pop('organizationId')

        if 'name' in difference2.keys():
            difference2.pop('name')

        if 'routes' in difference2.keys():
            difference2.pop('routes')

        if 'url' in difference2.keys():
            difference2.pop('url')

        if 'vlans' in difference2.keys():

            vlans = 0

            while vlans < len(difference2['vlans']):

                difference2['vlans'].pop(vlans, None)

                vlans = vlans + 1

        # print differences

        pprint.pprint(difference)
        pprint.pprint(difference2)


def getNetworkData(network_id):

        # This function makes all network config API calls
        # This data is then stored in a json for jsondiff

        response = dashboard.networks.getNetwork(
            network_id
        )
        response.update(dashboard.networks.getNetworkAlertsSettings(
            network_id
        ))
        response.update(dashboard.networks.getNetworkFirmwareUpgrades(
        network_id
        ))
        response.update([("floorPlans" , dashboard.networks.getNetworkFloorPlans(
        network_id
        ))])
        response.update(response = dashboard.networks.getNetworkGroupPolicies(
        network_id
        ))
        response.update(response = dashboard.networks.getNetworkMerakiAuthUsers(
        network_id
        ))
        response.update(dashboard.networks.getNetworkNetflow(
        network_id
        ))
        response.update(dashboard.networks.getNetworkSettings(
        network_id
        ))
        response.update(dashboard.networks.getNetworkSnmp(
        network_id
        ))
        response.update(dashboard.networks.getNetworkSyslogServers(
        network_id
        ))
        response.update(dashboard.networks.getNetworkTrafficAnalysis(
        network_id
        ))
        response.update(dashboard.networks.getNetworkWebhooksHttpServers(
        network_id
        ))
        response.update(dashboard.appliance.getNetworkApplianceConnectivityMonitoringDestinations(
        network_id
        ))
        response.update(dashboard.appliance.getNetworkApplianceContentFiltering(
        network_id
        ))
        response.update(dashboard.appliance.getNetworkApplianceFirewallCellularFirewallRules(
        network_id
        ))
        response.update([("services" , dashboard.appliance.getNetworkApplianceFirewallFirewalledServices(
        network_id
        ))])
        response.update(dashboard.appliance.getNetworkApplianceFirewallInboundFirewallRules(
        network_id
        ))
        response.update(dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules(
        network_id
        ))
        response.update(dashboard.appliance.getNetworkApplianceFirewallL7FirewallRules(
        network_id
        ))
        response.update(dashboard.appliance.getNetworkApplianceFirewallOneToManyNatRules(
        network_id
        ))
        response.update(dashboard.appliance.getNetworkApplianceFirewallOneToOneNatRules(
        network_id
        ))
        response.update(dashboard.appliance.getNetworkApplianceFirewallPortForwardingRules(
        network_id
        ))

        try:
            response.update(dashboard.appliance.getNetworkAppliancePorts(
            network_id
            ))

            response.update(dashboard.appliance.getNetworkApplianceTrafficShapingUplinkSelection(
            network_id
            ))

            response.update(dashboard.appliance.getNetworkApplianceTrafficShaping(
            network_id
            ))

            response.update(dashboard.appliance.getNetworkApplianceTrafficShapingCustomPerformanceClasses(
            network_id
            ))

            response.update(dashboard.appliance.getNetworkApplianceTrafficShapingRules(
            network_id
            ))

            response.update(dashboard.appliance.getNetworkApplianceTrafficShapingUplinkBandwidth(
            network_id
            ))

        except meraki.APIError as a:

            if "400" in str(a):

                    print("Correct appliance not present in this network")

        response.update(dashboard.appliance.getNetworkApplianceSecurityIntrusion(
        network_id
        ))
        response.update(dashboard.appliance.getNetworkApplianceSecurityMalware(
        network_id
        ))

        response.update([("routes", dashboard.appliance.getNetworkApplianceStaticRoutes(
        network_id
        ))])

        response.update([("vlans",dashboard.appliance.getNetworkApplianceVlans(
        network_id
        ))])

        try:
            response.update(dashboard.appliance.getNetworkApplianceVpnBgp(
            network_id
            ))
        except meraki.APIError as e:

            if "400" in str(e):

                print("Passthrough mode not enabled")

        response.update(dashboard.appliance.getNetworkApplianceVpnSiteToSiteVpn(
        network_id
        ))
        response.update(dashboard.appliance.getNetworkApplianceWarmSpare(
        network_id
        ))
        response.update(dashboard.switch.getNetworkSwitchAccessControlLists(
        network_id
        ))
        response.update([("accessPolicies", dashboard.switch.getNetworkSwitchAccessPolicies(
        network_id
        ))])

        try:
            response.update(dashboard.switch.getNetworkSwitchAlternateManagementInterface(
            network_id
            ))
        except meraki.APIError as e:

            if "400" in str(e):

                print("Alternate Management Interface on MS not supported")

        response.update(dashboard.switch.getNetworkSwitchDhcpServerPolicy(
        network_id
        ))
        response.update(dashboard.switch.getNetworkSwitchDscpToCosMappings(
        network_id
        ))
        response.update(dashboard.switch.getNetworkSwitchLinkAggregations(
        network_id
        ))
        response.update(dashboard.switch.getNetworkSwitchMtu(
        network_id
        ))
        response.update(dashboard.switch.getNetworkSwitchPortSchedules(
        network_id
        ))
        response.update(dashboard.switch.getNetworkSwitchQosRules(
        network_id
        ))
        response.update(dashboard.switch.getNetworkSwitchQosRulesOrder(
        network_id
        ))
        response.update(dashboard.switch.getNetworkSwitchSettings(
        network_id
        ))
        response.update(dashboard.switch.getNetworkSwitchStacks(
        network_id
        ))

        response.update(dashboard.switch.getNetworkSwitchRoutingMulticast(
        network_id
        ))

        response.update(dashboard.switch.getNetworkSwitchRoutingMulticastRendezvousPoints(
        network_id
        ))

        response.update(dashboard.switch.getNetworkSwitchRoutingOspf(
        network_id
        ))

        try:
            response.update(dashboard.switch.getNetworkSwitchStormControl(
            network_id
            ))

        except meraki.APIError as e:

            if "400" in str(e):

                print("Storm control mode not enabled")

        response.update(dashboard.switch.getNetworkSwitchStp(
        network_id
        ))
        try:
            response.update(dashboard.wireless.getNetworkWirelessBluetoothSettings(
            network_id
            ))
            response.update(dashboard.wireless.getNetworkWirelessAlternateManagementInterface(
            network_id
            ))
            response.update(dashboard.wireless.getNetworkWirelessBilling(
            network_id
            ))
            response.update(dashboard.wireless.getNetworkWirelessRfProfiles(
            network_id
            ))
            response.update(dashboard.wireless.getNetworkWirelessSettings(
            network_id
            ))
            ssids = dashboard.wireless.getNetworkWirelessSsids(
            network_id
            )

            response.update([("SSIDs", ssids)])

            for s in ssids:

                response.update(dashboard.wireless.getNetworkWirelessSsidBonjourForwarding(
                network_id, s['number']
                ))

                response.update(dashboard.wireless.getNetworkWirelessSsidDeviceTypeGroupPolicies(
                network_id, s['number']
                ))

                response.update(dashboard.wireless.getNetworkWirelessSsidEapOverride(
                network_id, s['number']
                ))

                response.update(dashboard.wireless.getNetworkWirelessSsidFirewallL3FirewallRules(
                network_id, s['number']
                ))

                response.update(dashboard.wireless.getNetworkWirelessSsidFirewallL7FirewallRules(
                network_id, s['number']
                ))

                response.update(dashboard.wireless.getNetworkWirelessSsidHotspot20(
                network_id, s['number']
                ))

                response.update([( "PSK", dashboard.wireless.getNetworkWirelessSsidIdentityPsks(
                network_id, s['number']
                ))])

                response.update(dashboard.wireless.getNetworkWirelessSsidSchedules(
                network_id, s['number']
                ))

                response.update(dashboard.wireless.getNetworkWirelessSsidSplashSettings(
                network_id, s['number']
                ))

                response.update(dashboard.wireless.getNetworkWirelessSsidTrafficShapingRules(
                network_id, s['number']
                ))

                response.update(dashboard.wireless.getNetworkWirelessSsidVpn(
                network_id, s['number']
                ))

        except meraki.APIError as e:

            if "400" in str(e):

                print("Not a wireless network")

        stacks = dashboard.switch.getNetworkSwitchStacks(
        network_id
        )

        response.update(stacks)

        for s in stacks:

            response.update(dashboard.switch.getNetworkSwitchStackRoutingStaticRoutes(
            network_id, s['id']
            ))

            interfaces = dashboard.switch.getNetworkSwitchStackRoutingInterfaces(
            network_id, s['id']
            )

            response.update(interfaces)

            for i in interfaces:

                response.update(dashboard.switch.getNetworkSwitchStackRoutingInterfaceDhcp(
                network_id, s['id'], i['interfaceId']
                ))

        return response


name1 = input("Enter original network name: ")
name2 = input("Enter cloned network name: ")

compareNetworks(name1, name2)


# PA23 - Clarks Summit Senior Living
# saveDeviceSettings(org_name)
# f = open('sample3.json')
# data = json.load(f)
# ensureDeviceSettings(org_name, data)
