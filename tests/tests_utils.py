
from unittest import TestCase
from .fixtures import xen_data
from novaagent import utils


import mock
import glob
import os


class ClientTest(object):
    """ Test class used for client mock """
    def __init__(self, return_value):
        self.return_data = return_value

    def list(self, path):
        return self.return_data

    def read(self, path):
        return self.return_data

    def write(self, event, data):
        return self.return_data

    def delete(self, path):
        return self.return_data


class TestHelpers(TestCase):
    def setUp(self):
        if not os.path.exists('/tmp/ifcfg-eth0'):
            with open('/tmp/ifcfg-eth0', 'a+') as f:
                f.write('This is a test file')
                os.utime('/tmp/ifcfg-eth0', None)

    def tearDown(self):
        files = glob.glob('/tmp/ifcfg-eth0*')
        for item in files:
            os.remove(item)

    def test_get_hostname_success_popen(self):
        client = ClientTest(xen_data.get_hostname(True))
        hostname = utils.get_hostname(client)
        self.assertEquals(
            hostname,
            'test-server',
            'Hostname does not match expected ouput'
        )

    def test_get_hostname_success_socket(self):
        with mock.patch('novaagent.utils.socket') as get:
            get.gethostname.return_value = (
                xen_data.get_hostname(False)
            )
            hostname = utils.get_hostname('dummy_client')

        self.assertEquals(
            hostname,
            'test-server',
            'Hostname does not match expected ouput'
        )

    def test_list_host_xen_events(self):
        check_events = ['748dee41-c47f-4ec7-b2cd-037e51da4031']
        client = ClientTest(xen_data.get_xen_host_events())
        event_list = utils.list_xen_events(client)
        self.assertEquals(
            event_list,
            check_events,
            'Event list does not match expected list'
        )

    def test_list_host_xen_events_exception(self):
        client = ClientTest(None)
        event_list = utils.list_xen_events(client)
        self.assertEquals(
            event_list,
            [],
            'Event list should be an empty list with exception'
        )

    def test_get_host_event(self):
        host_event_id = '748dee41-c47f-4ec7-b2cd-037e51da4031'
        event_check = {
            "name": "keyinit",
            "value": "68436575764933852815830951574296"
        }
        client = ClientTest(xen_data.get_xen_host_event_details())
        event_details = utils.get_xen_event(host_event_id, client)
        self.assertEquals(
            event_check,
            event_details,
            'Event details do not match expected value'
        )

    def test_get_host_event_exception(self):
        host_event_id = '748dee41-c47f-4ec7-b2cd-037e51da4031'
        client = ClientTest(None)
        event_details = utils.get_xen_event(host_event_id, client)
        self.assertEquals(
            event_details,
            None,
            'Event details should be None on exception'
        )

    def test_remove_xenhost_event_failure(self):
        host_event_id = '748dee41-c47f-4ec7-b2cd-037e51da4031'
        success = utils.remove_xenhost_event(host_event_id, 'dummy_client')
        self.assertEquals(
            success,
            False,
            'Return value was not False on failure'
        )

    def test_remove_xenhost_event_success(self):
        host_event_id = '748dee41-c47f-4ec7-b2cd-037e51da4031'
        client = ClientTest('')
        success = utils.remove_xenhost_event(host_event_id, client)
        self.assertEquals(
            success,
            True,
            'Return value was not True on success'
        )

    def test_update_xenguest_event_success(self):
        event_uuid = '748dee41-c47f-4ec7-b2cd-037e51da4031'
        client = ClientTest('')
        write_data = {"message": "", "returncode": "0"}
        success = utils.update_xenguest_event(event_uuid, write_data, client)
        self.assertEquals(
            success,
            True,
            'Return value was not True on success'
        )

    def test_update_xenguest_event_failure(self):
        event_uuid = '748dee41-c47f-4ec7-b2cd-037e51da4031'
        write_data = {"message": "", "returncode": "0"}
        success = utils.update_xenguest_event(
            event_uuid,
            write_data,
            'dummy_client'
        )
        self.assertEquals(
            success,
            False,
            'Return value was not False on failure'
        )

    def test_network_get_interfaces_success(self):
        mac_address = 'BC764E206C5B'
        client = ClientTest(xen_data.get_network_interface())
        network_info = utils.get_interface(mac_address, client)
        self.assertEquals(
            network_info,
            xen_data.check_network_interface(),
            'Network info returned was not the expected value'
        )

    def test_network_get_interfaces_failure(self):
        mac_address = 'BC764E206C5B'
        client = ClientTest(None)
        network_info = utils.get_interface(mac_address, client)
        self.assertEquals(
            network_info,
            None,
            'Network info should be None on error'
        )

    def test_network_get_mac_addresses_success(self):
        check_mac_addrs = ['BC764E206C5B', 'BC764E206C5A']
        client = ClientTest(xen_data.get_mac_addresses())
        mac_addrs = utils.list_xenstore_macaddrs(client)
        self.assertEquals(
            mac_addrs,
            check_mac_addrs,
            'Mac addrs returned do not match expected value'
        )

    def test_network_get_mac_addresses_exception(self):
        client = ClientTest(None)
        mac_addrs = utils.list_xenstore_macaddrs(client)
        self.assertEquals(
            mac_addrs,
            [],
            'Mac addrs returned is not empty list after error'
        )

    def test_network_get_mac_addresses_failure(self):
        client = ClientTest([])
        mac_addrs = utils.list_xenstore_macaddrs(client)
        self.assertEquals(
            mac_addrs,
            [],
            'Mac addrs returned is not empty list after error'
        )

    def test_get_os_interfaces(self):
        interfaces = ['lo', 'eth1', 'eth0']
        with mock.patch('novaagent.utils.os.path.exists') as os_path:
            os_path.return_value = True
            with mock.patch('novaagent.utils.os.listdir') as list_dir:
                list_dir.return_value = interfaces

                list_interfaces = utils.list_hw_interfaces()

        self.assertEqual(
            interfaces,
            list_interfaces,
            'Interfaces returned do not match expected return'
        )

    def test_get_os_interfaces_netifaces(self):
        interfaces = ['lo', 'eth1', 'eth0']
        with mock.patch('novaagent.utils.os.path.exists') as os_path:
            os_path.return_value = False
            with mock.patch('novaagent.utils.netifaces.interfaces') as netif:
                netif.return_value = interfaces

                list_interfaces = utils.list_hw_interfaces()

        self.assertEqual(
            interfaces,
            list_interfaces,
            'Interfaces returned do not match expected return'
        )

    def test_get_mac_address_from_system_string(self):
        check_mac_addr = 'BC764E206C5B'
        with mock.patch('novaagent.utils.socket.socket.fileno') as fileno:
            fileno.return_value = 3
            with mock.patch('novaagent.utils.fcntl.ioctl') as get_hex:
                get_hex.return_value = xen_data.FCNTL_INFO
                mac_address = utils.get_hw_addr('eth1')

        self.assertEqual(
            check_mac_addr,
            mac_address,
            'Mac addresses returned does not match expected value'
        )

    def test_get_mac_address_from_system_bytes(self):
        check_mac_addr = 'C2BC764E206C'
        with mock.patch('novaagent.utils.socket.socket.fileno') as fileno:
            fileno.return_value = 3
            with mock.patch('novaagent.utils.fcntl.ioctl') as get_hex:
                try:
                    get_hex.return_value = bytes(xen_data.FCNTL_INFO)
                except:
                    get_hex.return_value = bytes(xen_data.FCNTL_INFO, 'utf-8')

                mac_address = utils.get_hw_addr('eth1')

        self.assertEqual(
            check_mac_addr,
            mac_address,
            'Mac addresses returned does not match expected value'
        )

    def test_get_mac_address_from_system_error(self):
        with mock.patch('novaagent.utils.socket.socket.fileno') as fileno:
            fileno.return_value = 3
            with mock.patch('novaagent.utils.fcntl.ioctl') as get_hex:
                get_hex.side_effect = IOError
                utils.HAS_NETIFACES = False
                mac_address = utils.get_hw_addr('eth1')

        self.assertEqual(
            False,
            mac_address,
            'Mac address returned should be false on error'
        )

    def test_get_mac_address_from_system_netifaces(self):
        check_mac_addr = 'BC764E205A79'
        with mock.patch('novaagent.utils.socket.socket.fileno') as fileno:
            fileno.return_value = 3
            with mock.patch('novaagent.utils.fcntl.ioctl') as get_hex:
                get_hex.side_effect = IOError
                with mock.patch('novaagent.utils.netifaces') as interfaces:
                    interfaces.ifaddresses.return_value = (
                        xen_data.get_iface_from_netifaces()
                    )
                    interfaces.AF_LINK = 17
                    utils.HAS_NETIFACES = True
                    mac_address = utils.get_hw_addr('eth1')

        self.assertEqual(
            check_mac_addr,
            mac_address,
            'Mac addresses returned does not match expected value'
        )

    def test_get_mac_address_from_system_netifaces_failure(self):
        with mock.patch('novaagent.utils.socket.socket.fileno') as fileno:
            fileno.return_value = 3
            with mock.patch('novaagent.utils.fcntl.ioctl') as get_hex:
                get_hex.side_effect = IOError
                with mock.patch('novaagent.utils.netifaces') as interfaces:
                    interfaces.ifaddresses.return_value = (
                        xen_data.get_iface_from_netifaces()
                    )
                    interfaces.AF_LINK = 99
                    utils.HAS_NETIFACES = True
                    mac_address = utils.get_hw_addr('eth1')

        self.assertEqual(
            False,
            mac_address,
            'Mac addresses returned should be false on error'
        )

    def test_netmask_to_prefix_24(self):
        cidr = utils.netmask_to_prefix('255.255.255.0')
        self.assertEqual(
            cidr,
            24,
            'Cidr returned does not match expected value'
        )
        cidr = utils.netmask_to_prefix('255.255.0.0')
        self.assertEqual(
            cidr,
            16,
            'Cidr returned does not match expected value'
        )

    def test_network_remove_files(self):
        net_config_dir = '/etc/sysconfig/network-scripts'
        interface_file_prefix = 'ifcfg-'

        with mock.patch('novaagent.utils.os.listdir') as listdir:
            listdir.return_value = ['lo', 'eth0']
            with mock.patch('novaagent.utils.glob.glob') as files:
                files.return_value = [
                    '/etc/sysconfig/network-scripts/ifcfg-eth1',
                    '/etc/sysconfig/network-scripts/ifcfg-lo',
                    '/etc/sysconfig/network-scripts/ifcfg-eth0'
                ]
                remove_files = utils.get_ifcfg_files_to_remove(
                    net_config_dir,
                    interface_file_prefix
                )

        self.assertEqual(
            remove_files,
            ['/etc/sysconfig/network-scripts/ifcfg-eth1'],
            'Remove files returned is not the expected value'
        )

    def test_move_interface_file_for_backup(self):
        rename_file = '/tmp/ifcfg-eth0'
        utils.move_file(rename_file)

        files = glob.glob('/tmp/ifcfg-eth0.*.*.bak')
        self.assertEqual(
            len(files),
            1,
            'Did not find any files'
        )
        self.assertIn(
            'ifcfg-eth0',
            files[0],
            'Did not find the original filename in renamed file path'
        )

    def test_move_interface_file_for_backup_no_file(self):
        rename_file = '/tmp/ifcfg-eth0'
        os.remove(rename_file)
        utils.move_file(rename_file)
        assert True, 'Move interface did not generate error'

    def test_rename_interface_file_success(self):
        rename_file = '/tmp/ifcfg-eth0'
        utils.backup_file(rename_file)

        files = glob.glob('/tmp/ifcfg-eth0.*.*.bak')
        self.assertEqual(
            len(files),
            1,
            'Did not find any files'
        )
        self.assertIn(
            'ifcfg-eth0',
            files[0],
            'Did not find the original filename in renamed file path'
        )

    def test_backup_file_failure(self):
        rename_file = '/tmp/ifcfg-eth0'
        os.remove(rename_file)
        utils.backup_file(rename_file)
        assert True, 'Move interface did not generate error'

    def test_encoding_to_bytes(self):
        test_string = 'this is a test'
        compare_string = b'this is a test'
        test = utils.encode_to_bytes(test_string)
        self.assertEqual(
            compare_string,
            test,
            'Byte strings do not match as expected'
        )
