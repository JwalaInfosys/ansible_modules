# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Mikhail Yohman (@fragmentedpacket) <mikhail.yohman@gmail.com>
# Copyright: (c) 2018, David Gomez (@amb1s1) <david.gomez@networktocode.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

__metaclass__ = type

# Import necessary packages
import traceback
import re
from itertools import chain
from ansible.module_utils.compat import ipaddress
from ansible.module_utils._text import to_text

# from ._text import to_native
from ansible.module_utils._text import to_native
from ansible.module_utils.common.collections import is_iterable
from ansible.module_utils.basic import AnsibleModule, missing_required_lib

PYNETBOX_IMP_ERR = None
try:
    import pynetbox

    HAS_PYNETBOX = True
except ImportError:
    PYNETBOX_IMP_ERR = traceback.format_exc()
    HAS_PYNETBOX = False

# Used to map endpoints to applications dynamically
API_APPS_ENDPOINTS = dict(
    circuits=["circuits", "circuit_types", "circuit_terminations", "providers"],
    dcim=[
        "device_bays",
        "devices",
        "device_roles",
        "device_types",
        "interfaces",
        "inventory_items",
        "manufacturers",
        "platforms",
        "racks",
        "rack_groups",
        "rack_roles",
        "regions",
        "sites",
    ],
    extras=[],
    ipam=[
        "aggregates",
        "ip_addresses",
        "prefixes",
        "services",
        "rirs",
        "roles",
        "vlans",
        "vlan_groups",
        "vrfs",
        "services",
    ],
    secrets=[],
    tenancy=["tenants", "tenant_groups"],
    virtualization=["cluster_groups", "cluster_types", "clusters", "virtual_machines"],
)

# Used to normalize data for the respective query types used to find endpoints
QUERY_TYPES = dict(
    circuit="cid",
    circuit_termination="circuit",
    circuit_type="slug",
    cluster="name",
    cluster_group="slug",
    cluster_type="slug",
    device="name",
    device_role="slug",
    device_type="slug",
    group="slug",
    installed_device="name",
    manufacturer="slug",
    nat_inside="address",
    nat_outside="address",
    parent_region="slug",
    platform="slug",
    prefix_role="slug",
    primary_ip="address",
    primary_ip4="address",
    primary_ip6="address",
    provider="slug",
    rack="name",
    rack_group="slug",
    rack_role="slug",
    region="slug",
    rir="slug",
    slug="slug",
    site="slug",
    tenant="name",
    tenant_group="slug",
    time_zone="timezone",
    virtual_machine="name",
    vlan="name",
    vlan_group="slug",
    vlan_role="name",
    vrf="name",
)

# Specifies keys within data that need to be converted to ID and the endpoint to be used when queried
CONVERT_TO_ID = dict(
    circuit="circuits",
    circuit_type="circuit_types",
    circuit_termination="circuit_terminations",
    cluster="clusters",
    cluster_group="cluster_groups",
    cluster_type="cluster_types",
    device="devices",
    device_role="device_roles",
    device_type="device_types",
    group="tenant_groups",
    installed_device="devices",
    interface="interfaces",
    ip_addresses="ip_addresses",
    lag="interfaces",
    manufacturer="manufacturers",
    nat_inside="ip_addresses",
    nat_outside="ip_addresses",
    platform="platforms",
    parent_region="regions",
    prefix_role="roles",
    primary_ip="ip_addresses",
    primary_ip4="ip_addresses",
    primary_ip6="ip_addresses",
    provider="providers",
    rack="racks",
    rack_group="rack_groups",
    rack_role="rack_roles",
    region="regions",
    rir="rirs",
    services="services",
    site="sites",
    tagged_vlans="vlans",
    tenant="tenants",
    tenant_group="tenant_groups",
    untagged_vlan="vlans",
    virtual_machine="virtual_machines",
    virtual_machine_role="device_roles",
    vlan="vlans",
    vlan_group="vlan_groups",
    vlan_role="roles",
    vrf="vrfs",
)

ENDPOINT_NAME_MAPPING = {
    "aggregates": "aggregate",
    "circuit_terminations": "circuit_termination",
    "circuit_types": "circuit_type",
    "circuits": "circuit",
    "clusters": "cluster",
    "cluster_groups": "cluster_group",
    "cluster_types": "cluster_type",
    "device_bays": "device_bay",
    "devices": "device",
    "device_roles": "device_role",
    "device_types": "device_type",
    "interfaces": "interface",
    "inventory_items": "inventory_item",
    "ip_addresses": "ip_address",
    "manufacturers": "manufacturer",
    "platforms": "platform",
    "prefixes": "prefix",
    "providers": "provider",
    "racks": "rack",
    "rack_groups": "rack_group",
    "rack_roles": "rack_role",
    "regions": "region",
    "rirs": "rir",
    "roles": "role",
    "services": "services",
    "sites": "site",
    "tenants": "tenant",
    "tenant_groups": "tenant_group",
    "virtual_machines": "virtual_machine",
    "vlans": "vlan",
    "vlan_groups": "vlan_group",
    "vrfs": "vrf",
}

ALLOWED_QUERY_PARAMS = {
    "aggregate": set(["prefix", "rir"]),
    "circuit": set(["cid"]),
    "circuit_type": set(["slug"]),
    "circuit_termination": set(["circuit", "term_side"]),
    "cluster": set(["name", "type"]),
    "cluster_group": set(["slug"]),
    "cluster_type": set(["slug"]),
    "device_bay": set(["name", "device"]),
    "device": set(["name"]),
    "device_role": set(["slug"]),
    "device_type": set(["slug"]),
    "installed_device": set(["name"]),
    "interface": set(["name", "device", "virtual_machine"]),
    "inventory_item": set(["name", "device"]),
    "ip_address": set(["address", "vrf"]),
    "ip_addresses": set(["address", "vrf", "device"]),
    "lag": set(["name"]),
    "manufacturer": set(["slug"]),
    "nat_inside": set(["vrf", "address"]),
    "parent_region": set(["slug"]),
    "platform": set(["slug"]),
    "prefix": set(["prefix", "vrf"]),
    "primary_ip4": set(["address", "vrf"]),
    "primary_ip6": set(["address", "vrf"]),
    "provider": set(["slug"]),
    "rack": set(["name", "site"]),
    "rack_group": set(["slug"]),
    "rack_role": set(["slug"]),
    "region": set(["slug"]),
    "rir": set(["slug"]),
    "role": set(["slug"]),
    "services": set(["device", "virtual_machine", "name"]),
    "site": set(["slug"]),
    "tagged_vlans": set(["name", "site", "vlan_group", "tenant"]),
    "tenant": set(["name"]),
    "tenant_group": set(["name"]),
    "untagged_vlan": set(["name", "site", "vlan_group", "tenant"]),
    "virtual_machine": set(["name", "cluster"]),
    "vlan": set(["name", "site", "tenant", "vlan_group"]),
    "vlan_group": set(["slug", "site"]),
    "vrf": set(["name", "tenant"]),
}

QUERY_PARAMS_IDS = set(
    [
        "circuit",
        "cluster",
        "device",
        "group",
        "rir",
        "vrf",
        "site",
        "tenant",
        "type",
        "virtual_machine",
    ]
)

REQUIRED_ID_FIND = {
    "circuits": set(["status"]),
    "devices": set(["status", "face"]),
    "device_types": set(["subdevice_role"]),
    "interfaces": set(["form_factor", "mode"]),
    "ip_addresses": set(["status", "role"]),
    "prefixes": set(["status"]),
    "racks": set(["status", "outer_unit", "type"]),
    "services": set(["protocol"]),
    "sites": set(["status"]),
    "virtual_machines": set(["status", "face"]),
    "vlans": set(["status"]),
}

# This is used to map non-clashing keys to Netbox API compliant keys to prevent bad logic in code for similar keys but different modules
CONVERT_KEYS = {
    "circuit_type": "type",
    "cluster_type": "type",
    "cluster_group": "group",
    "parent_region": "parent",
    "prefix_role": "role",
    "rack_group": "group",
    "rack_role": "role",
    "tenant_group": "group",
    "virtual_machine_role": "role",
    "vlan_role": "role",
    "vlan_group": "group",
}

# This is used to dynamically conver name to slug on endpoints requiring a slug
SLUG_REQUIRED = {
    "circuit_types",
    "cluster_groups",
    "cluster_types",
    "device_roles",
    "device_types",
    "ipam_roles",
    "rack_groups",
    "rack_roles",
    "regions",
    "rirs",
    "roles",
    "manufacturers",
    "platforms",
    "providers",
    "vlan_groups",
}


NETBOX_ARG_SPEC = dict(
    netbox_url=dict(type="str", required=True),
    netbox_token=dict(type="str", required=True, no_log=True),
    state=dict(required=False, default="present", choices=["present", "absent"]),
    validate_certs=dict(type="bool", default=True),
)


class NetboxModule(object):
    """
    Initialize connection to Netbox, sets AnsibleModule passed in to
    self.module to be used throughout the class
    :params module (obj): Ansible Module object
    :params endpoint (str): Used to tell class which endpoint the logic needs to follow
    :params nb_client (obj): pynetbox.api object passed in (not required)
    """

    def __init__(self, module, endpoint, nb_client=None):
        self.module = module
        self.state = self.module.params["state"]
        self.check_mode = self.module.check_mode
        self.endpoint = endpoint
        self.version = None

        if not HAS_PYNETBOX:
            self.module.fail_json(
                msg=missing_required_lib("pynetbox"), exception=PYNETBOX_IMP_ERR
            )
        # These should not be required after making connection to Netbox
        url = self.module.params["netbox_url"]
        token = self.module.params["netbox_token"]
        ssl_verify = self.module.params["validate_certs"]

        # Attempt to initiate connection to Netbox
        if nb_client is None:
            self.nb = self._connect_netbox_api(url, token, ssl_verify)
        else:
            self.nb = nb_client

        # These methods will normalize the regular data
        cleaned_data = self._remove_arg_spec_default(module.params["data"])
        norm_data = self._normalize_data(cleaned_data)
        choices_data = self._change_choices_id(self.endpoint, norm_data)
        data = self._find_ids(choices_data)
        self.data = self._convert_identical_keys(data)

    def _connect_netbox_api(self, url, token, ssl_verify):
        try:
            nb = pynetbox.api(url, token=token, ssl_verify=ssl_verify)
            try:
                self.version = float(nb.version)
            except AttributeError:
                self.module.fail_json(msg="Must have pynetbox >=4.1.0")
            except Exception:
                self.module.fail_json(
                    msg="Failed to establish connection to Netbox API"
                )
            return nb
        except Exception:
            self.module.fail_json(msg="Failed to establish connection to Netbox API")

    def _nb_endpoint_get(self, nb_endpoint, query_params, search_item):
        try:
            response = nb_endpoint.get(**query_params)
        except pynetbox.RequestError as e:
            self._handle_errors(msg=e.error)
        except ValueError:
            self._handle_errors(
                msg="More than one result returned for %s" % (search_item)
            )

        return response

    def _handle_errors(self, msg):
        """
        Returns message and changed = False
        :params msg (str): Message indicating why there is no change
        """
        if msg:
            self.module.fail_json(msg=msg, changed=False)

    def _build_diff(self, before=None, after=None):
        """Builds diff of before and after changes"""
        return {"before": before, "after": after}

    def _convert_identical_keys(self, data):
        """
        Used to change non-clashing keys for each module into identical keys that are required
        to be passed to pynetbox
        ex. rack_role back into role to pass to Netbox
        Returns data
        :params data (dict): Data dictionary after _find_ids method ran
        """
        if self.version and self.version >= 2.7:
            if data.get("form_factor"):
                data["type"] = data.pop("form_factor")
        for key in data:
            if key in CONVERT_KEYS:
                new_key = CONVERT_KEYS[key]
                value = data.pop(key)
                data[new_key] = value

        return data

    def _remove_arg_spec_default(self, data):
        """Used to remove any data keys that were not provided by user, but has the arg spec
        default values
        """
        new_dict = dict()
        for k, v in data.items():
            if v is not None:
                new_dict[k] = v

        return new_dict

    def _get_query_param_id(self, match, data):
        """Used to find IDs of necessary searches when required under _build_query_params
        :returns id (int) or data (dict): Either returns the ID or original data passed in
        :params match (str): The key within the user defined data that is required to have an ID
        :params data (dict): User defined data passed into the module
        """
        if isinstance(data.get(match), int):
            return data[match]
        else:
            endpoint = CONVERT_TO_ID[match]
            app = self._find_app(endpoint)
            nb_app = getattr(self.nb, app)
            nb_endpoint = getattr(nb_app, endpoint)

            query_params = {QUERY_TYPES.get(match): data[match]}
            result = self._nb_endpoint_get(nb_endpoint, query_params, match)

            if result:
                return result.id
            else:
                return data

    def _build_query_params(self, parent, module_data, child=None):
        """
        :returns dict(query_dict): Returns a query dictionary built using mappings to dynamically
        build available query params for Netbox endpoints
        :params parent(str): This is either a key from `_find_ids` or a string passed in to determine
        which keys in the data that we need to use to construct `query_dict`
        :params module_data(dict): Uses the data provided to the Netbox module
        :params child(dict): This is used within `_find_ids` and passes the inner dictionary
        to build the appropriate `query_dict` for the parent
        """
        query_dict = dict()
        query_params = ALLOWED_QUERY_PARAMS.get(parent)

        if child:
            matches = query_params.intersection(set(child.keys()))
        else:
            matches = query_params.intersection(set(module_data.keys()))

        for match in matches:
            if match in QUERY_PARAMS_IDS:
                if child:
                    query_id = self._get_query_param_id(match, child)
                else:
                    query_id = self._get_query_param_id(match, module_data)
                query_dict.update({match + "_id": query_id})
            else:
                if child:
                    value = child.get(match)
                else:
                    value = module_data.get(match)
                query_dict.update({match: value})

        if parent == "lag":
            if not child:
                query_dict["name"] = module_data["lag"]
            intf_type = self._fetch_choice_value(
                "Link Aggregation Group (LAG)", "interfaces"
            )
            query_dict.update({"form_factor": intf_type})
            if isinstance(module_data["device"], int):
                query_dict.update({"device_id": module_data["device"]})
            else:
                query_dict.update({"device": module_data["device"]})

        elif parent == "prefix" and module_data.get("parent"):
            query_dict.update({"prefix": module_data["parent"]})

        elif parent == "ip_addreses":
            if isinstance(module_data["device"], int):
                query_dict.update({"device_id": module_data["device"]})
            else:
                query_dict.update({"device": module_data["device"]})

        query_dict = self._convert_identical_keys(query_dict)
        return query_dict

    def _fetch_choice_value(self, search, endpoint):
        app = self._find_app(endpoint)
        nb_app = getattr(self.nb, app)
        nb_endpoint = getattr(nb_app, endpoint)
        endpoint_choices = nb_endpoint.choices()

        choices = [x for x in chain.from_iterable(endpoint_choices.values())]

        for item in choices:
            if item["display_name"].lower() == search.lower():
                return item["value"]
            elif item["value"] == search.lower():
                return item["value"]
        self._handle_errors(
            msg="%s was not found as a valid choice for %s" % (search, endpoint)
        )

    def _change_choices_id(self, endpoint, data):
        """Used to change data that is static and under _choices for the application.
        ex. DEVICE_STATUS
        :returns data (dict): Returns the user defined data back with updated fields for _choices
        :params endpoint (str): The endpoint that will be used for mapping to required _choices
        :params data (dict): User defined data passed into the module
        """
        if REQUIRED_ID_FIND.get(endpoint):
            required_choices = REQUIRED_ID_FIND[endpoint]
            for choice in required_choices:
                if data.get(choice):
                    if isinstance(data[choice], int):
                        continue
                    choice_value = self._fetch_choice_value(data[choice], endpoint)
                    data[choice] = choice_value

        return data

    def _find_app(self, endpoint):
        """Dynamically finds application of endpoint passed in using the
        API_APPS_ENDPOINTS for mapping
        :returns nb_app (str): The application the endpoint lives under
        :params endpoint (str): The endpoint requiring resolution to application
        """
        for k, v in API_APPS_ENDPOINTS.items():
            if endpoint in v:
                nb_app = k
        return nb_app

    def _find_ids(self, data):
        """Will find the IDs of all user specified data if resolvable
        :returns data (dict): Returns the updated dict with the IDs of user specified data
        :params data (dict): User defined data passed into the module
        """
        for k, v in data.items():
            if k in CONVERT_TO_ID:
                endpoint = CONVERT_TO_ID[k]
                search = v
                app = self._find_app(endpoint)
                nb_app = getattr(self.nb, app)
                nb_endpoint = getattr(nb_app, endpoint)

                if isinstance(v, dict):
                    if k == "interface" and v.get("virtual_machine"):
                        nb_app = getattr(self.nb, "virtualization")
                        nb_endpoint = getattr(nb_app, endpoint)
                    query_params = self._build_query_params(k, data, v)
                    query_id = self._nb_endpoint_get(nb_endpoint, query_params, k)

                elif isinstance(v, list):
                    id_list = list()
                    for list_item in v:
                        norm_data = self._normalize_data(list_item)
                        temp_dict = self._build_query_params(k, data, norm_data)
                        query_id = self._nb_endpoint_get(nb_endpoint, temp_dict, k)
                        if query_id:
                            id_list.append(query_id.id)
                        else:
                            self._handle_errors(msg="%s not found" % (list_item))

                else:
                    query_params = {QUERY_TYPES.get(k, "q"): search}
                    query_id = self._nb_endpoint_get(nb_endpoint, query_params, k)

                if isinstance(v, list):
                    data[k] = id_list
                elif isinstance(v, int):
                    pass
                elif query_id:
                    data[k] = query_id.id
                else:
                    self._handle_errors(msg="Could not resolve id of %s: %s" % (k, v))

        return data

    def _to_slug(self, value):
        """
        :returns slug (str): Slugified value
        :params value (str): Value that needs to be changed to slug format
        """
        if value is None:
            return value
        elif isinstance(value, int):
            return value
        else:
            removed_chars = re.sub(r"[^\-\.\w\s]", "", value)
            convert_chars = re.sub(r"[\-\.\s]+", "-", removed_chars)
            return convert_chars.strip().lower()

    def _normalize_data(self, data):
        """
        :returns data (dict): Normalized module data to formats accepted by Netbox searches
        such as changing from user specified value to slug
        ex. Test Rack -> test-rack
        :params data (dict): Original data from Netbox module
        """
        for k, v in data.items():
            if isinstance(v, dict):
                for subk, subv in v.items():
                    sub_data_type = QUERY_TYPES.get(subk, "q")
                    if sub_data_type == "slug":
                        data[k][subk] = self._to_slug(subv)
            else:
                data_type = QUERY_TYPES.get(k, "q")
                if data_type == "slug":
                    data[k] = self._to_slug(v)
                elif data_type == "timezone":
                    if " " in v:
                        data[k] = v.replace(" ", "_")
        if self.endpoint == "sites":
            site_slug = self._to_slug(data["name"])
            data["slug"] = site_slug

        return data

    def _create_netbox_object(self, nb_endpoint, data):
        """Create a Netbox object.
        :returns tuple(serialized_nb_obj, diff): tuple of the serialized created
        Netbox object and the Ansible diff.
        """
        if self.check_mode:
            nb_obj = data
        else:
            try:
                nb_obj = nb_endpoint.create(data)
            except pynetbox.RequestError as e:
                self._handle_errors(msg=e.error)

        diff = self._build_diff(before={"state": "absent"}, after={"state": "present"})
        return nb_obj, diff

    def _delete_netbox_object(self):
        """Delete a Netbox object.
        :returns diff (dict): Ansible diff
        """
        if not self.check_mode:
            try:
                self.nb_object.delete()
            except pynetbox.RequestError as e:
                self._handle_errors(msg=e.error)

        diff = self._build_diff(before={"state": "present"}, after={"state": "absent"})
        return diff

    def _update_netbox_object(self, data):
        """Update a Netbox object.
        :returns tuple(serialized_nb_obj, diff): tuple of the serialized updated
        Netbox object and the Ansible diff.
        """
        serialized_nb_obj = self.nb_object.serialize()
        updated_obj = serialized_nb_obj.copy()
        updated_obj.update(data)
        if serialized_nb_obj == updated_obj:
            return serialized_nb_obj, None
        else:
            data_before, data_after = {}, {}
            for key in data:
                try:
                    if serialized_nb_obj[key] != updated_obj[key]:
                        data_before[key] = serialized_nb_obj[key]
                        data_after[key] = updated_obj[key]
                except KeyError:
                    self._handle_errors(
                        msg="%s does not exist on existing object. Check to make sure valid field."
                        % (key)
                    )

            if not self.check_mode:
                self.nb_object.update(data)
                updated_obj = self.nb_object.serialize()

            diff = self._build_diff(before=data_before, after=data_after)
            return updated_obj, diff

    def _ensure_object_exists(self, nb_endpoint, endpoint_name, name, data):
        """Used when `state` is present to make sure object exists or if the object exists
        that it is updated
        :params nb_endpoint (pynetbox endpoint object): This is the nb endpoint to be used
        to create or update the object
        :params endpoint_name (str): Endpoint name that was created/updated. ex. device
        :params name (str): Name of the object
        :params data (dict): User defined data passed into the module
        """
        if not self.nb_object:
            self.nb_object, diff = self._create_netbox_object(nb_endpoint, data)
            self.result["msg"] = "%s %s created" % (endpoint_name, name)
            self.result["changed"] = True
            self.result["diff"] = diff
        else:
            self.nb_object, diff = self._update_netbox_object(data)
            if self.nb_object is False:
                self._handle_errors(
                    msg="Request failed, couldn't update device: %s" % name
                )
            if diff:
                self.result["msg"] = "%s %s updated" % (endpoint_name, name)
                self.result["changed"] = True
                self.result["diff"] = diff
            else:
                self.result["msg"] = "%s %s already exists" % (endpoint_name, name)

    def _ensure_object_absent(self, endpoint_name, name):
        """Used when `state` is absent to make sure object does not exist
        :params endpoint_name (str): Endpoint name that was created/updated. ex. device
        :params name (str): Name of the object
        """
        if self.nb_object:
            diff = self._delete_netbox_object()
            self.result["msg"] = "%s %s deleted" % (endpoint_name, name)
            self.result["changed"] = True
            self.result["diff"] = diff
        else:
            self.result["msg"] = "%s %s already absent" % (endpoint_name, name)

    def run(self):
        """
        Must be implemented in subclasses
        """
        raise NotImplementedError


class NetboxAnsibleModule(AnsibleModule):
    """
    Creating this due to needing to override some functionality to provide required_together, required_if
    and will be able to override more in the future.
    This is due to the Netbox modules having the module arguments within a key in the argument spec, using suboptions rather than
    having all module arguments within the regular argument spec.

    Didn't want to change that functionality of the Netbox modules as its disruptive and we're required to send a specific payload
    to the Netbox API
    """

    def __init__(
        self,
        argument_spec,
        bypass_checks=False,
        no_log=False,
        mutually_exclusive=None,
        required_together=None,
        required_one_of=None,
        add_file_common_args=False,
        supports_check_mode=False,
        required_if=None,
        required_by=None,
    ):
        super().__init__(
            argument_spec,
            bypass_checks=False,
            no_log=False,
            mutually_exclusive=None,
            required_together=None,
            required_one_of=None,
            add_file_common_args=False,
            supports_check_mode=supports_check_mode,
            required_if=required_if,
            required_by=None,
        )

    def _check_required_if(self, spec, param=None):
        """ ensure that parameters which conditionally required are present """
        if spec is None:
            return

        if param is None:
            param = self.params

        try:
            self.check_required_if(spec, param)
        except TypeError as e:
            msg = to_native(e)
            if self._options_context:
                msg += " found in %s" % " -> ".join(self._options_context)
            self.fail_json(msg=msg)

    def check_required_if(self, requirements, module_parameters):
        results = []
        if requirements is None:
            return results

        for req in requirements:
            missing = {}
            missing["missing"] = []
            max_missing_count = 0
            is_one_of = False
            if len(req) == 4:
                key, val, requirements, is_one_of = req
            else:
                key, val, requirements = req

            # is_one_of is True at least one requirement should be
            # present, else all requirements should be present.
            if is_one_of:
                max_missing_count = len(requirements)
                missing["requires"] = "any"
            else:
                missing["requires"] = "all"

            if key in module_parameters and module_parameters[key] == val:
                for check in requirements:
                    count = self.count_terms(check, module_parameters["data"])
                    if count == 0:
                        missing["missing"].append(check)
            if len(missing["missing"]) and len(missing["missing"]) >= max_missing_count:
                missing["parameter"] = key
                missing["value"] = val
                missing["requirements"] = requirements
                results.append(missing)

        if results:
            for missing in results:
                msg = "%s is %s but %s of the following are missing: %s" % (
                    missing["parameter"],
                    missing["value"],
                    missing["requires"],
                    ", ".join(missing["missing"]),
                )
                raise TypeError(to_native(msg))

        return results

    def count_terms(self, terms, module_parameters):
        """Count the number of occurrences of a key in a given dictionary
        :arg terms: String or iterable of values to check
        :arg module_parameters: Dictionary of module parameters
        :returns: An integer that is the number of occurrences of the terms values
            in the provided dictionary.
        """

        if not is_iterable(terms):
            terms = [terms]

        return len(set(terms).intersection(module_parameters))
