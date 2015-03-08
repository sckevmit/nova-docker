import mock, sys

class MockContrailVRouterApi(mock.MagicMock):
    def __init__(self, *a, **kw):
        super(MockContrailVRouterApi, self).__init__()
        self._args = a
        self._dict = kw
        self._vifs = {}

    def add_port(self, vm_uuid_str, vif_uuid_str, interface_name,
            mac_address, **kwargs):
        if vm_uuid_str not in self._vifs:
            self._vifs[vif_uuid_str] = dict(vm=vm_uuid_str,
                    intf=interface_name,
                    mac=mac_address)
            self._vifs[vm_uuid_str].update(kwargs)
            return self._vifs[vif_uuid_str]

    def delete_port(self, vif_uuid_str):
        if vif_uuid_str in self._vifs:
            del self._vifs[vif_uuid_str]
        

mock_pkg = mock.MagicMock(name='mock_contrail_vrouter_api')
mock_mod = mock.MagicMock(name='mock_vrouter_api')
mock_cls = mock.MagicMock(name='MockOpenContrailVIFDriver',
        side_effect=MockContrailVRouterApi)
mock_mod.OpenContrailVIFDriver = mock_cls
mock_pkg.vrouter_api = mock_mod

sys.modules['contrail_vrouter_api'] = mock_pkg
sys.modules['contrail_vrouter_api.vrouter_api'] = mock_mod

from novadocker.virt.docker.opencontrail import OpenContrailVIFDriver
#from test_vifs import DockerGenericVIFDriverTestCase
#class DockerOpenContrailVIFDriverTestCase(DockerGenericVIFDriverTestCase):
from nova import test
from novadocker.virt.docker import driver as docker_driver
from nova.network import model as network_model


class DockerOpenContrailVIFDriverTestCase(test.TestCase):
    def setUp(self):
        super(DockerOpenContrailVIFDriverTestCase, self).setUp()
        docker_driver.CONF.set_override('vif_driver',
            'novadocker.virt.docker.opencontrail.OpenContrailVIFDriver',
            group='docker')

    def test_plug_vrouter(self):
        vid = '920be1f4-2b98-411e-890a-69bcabb2a5a0'
        address = '10.1.2.1'
        calls = [
            mock.call('ip', 'link', 'add', 'veth%s' % vid[:8],
                    'type', 'veth', 'peer', 'name', 
                    'ns%s' % vid[:8], run_as_root=True),
            mock.call('ip', 'link', 'set', 'ns%s' % vid[:8],
                    'address', address, run_as_root=True),
            ]
        network_info = [network_model.VIF(id=vid,
                address=address)]
        with mock.patch('nova.utils.execute') as ex:
            driver = docker_driver.DockerDriver(object)
            driver.plug_vifs({'name': 'fake_instance'}, network_info)
            ex.assert_has_calls(calls)
        
    def test_plug_two_vrouters(self):
        vid1 = '921be2f4-2b98-411e-890a-69bcabb2a5a1'
        address1 = '10.1.2.2'
        vid2 = '922be3f4-2b98-411e-890a-69bcabb2a5a2'
        address2 = '10.1.2.3'
        calls = [
            mock.call('ip', 'link', 'add', 'veth%s' % vid1[:8],
                    'type', 'veth', 'peer', 'name', 
                    'ns%s' % vid1[:8], run_as_root=True),
            mock.call('ip', 'link', 'set', 'ns%s' % vid1[:8],
                    'address', address1, run_as_root=True),
            mock.call('ip', 'link', 'add', 'veth%s' % vid2[:8],
                    'type', 'veth', 'peer', 'name', 
                    'ns%s' % vid2[:8], run_as_root=True),
            mock.call('ip', 'link', 'set', 'ns%s' % vid2[:8],
                    'address', address2, run_as_root=True),
            ]
        network_info = [network_model.VIF(id=vid1, address=address1),
                        network_model.VIF(id=vid2, address=address2)]
        with mock.patch('nova.utils.execute') as ex:
            driver = docker_driver.DockerDriver(object)
            driver.plug_vifs({'name': 'fake_instance'}, network_info)
            ex.assert_has_calls(calls)

    def test_unplug_vrouter(self):
        vid = '920be1f4-2b98-411e-890a-69bcabb2a5a0'
        address = '10.1.2.1'
        calls = [
            mock.call('ip', 'link', 'delete', 'veth%s' % vid[:8],
                    run_as_root=True),
            ]
        network_info = [network_model.VIF(id=vid, address=address)]
        with mock.patch('nova.utils.execute') as ex:
            driver = docker_driver.DockerDriver(object)
            driver.unplug_vifs({'name': 'fake_instance'}, network_info)
            ex.assert_has_calls(calls)
        
