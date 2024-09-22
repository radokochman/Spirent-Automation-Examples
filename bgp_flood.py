import time
from stcrestclient import stchttp

# Connection variables
spirent_box = "10.0.0.1"
stc_server = "10.0.1.1"
port = 8888

# Session variables
user_name = "radokochman"
session_name = "Script"
session_id = f"{session_name} - {user_name}"

# BGP variables
generated_bgp_routes = 225000
stormwind_router_id = "192.168.255.2"
stormwind_as = 64512
ironforge_as = 64513
generated_prefixes_start_ip = "100.0.0.0"

# IP addresses
ironforge_int_ip = "192.168.255.1"
stormwind_int_ip = "192.168.255.2"


stc_session = stchttp.StcHttp(stc_server, port=port)
stc_session.new_session(
    user_name=user_name, session_name=session_name, kill_existing=True
)
stc_project = stc_session.create("project")

stc_session.connect(spirent_box)

port_location = "//10.0.0.1/1/3"
port3_handler = stc_session.create("Port", under=stc_project, Location=port_location)


# Create Emulated Device
stormwind_device = stc_session.create(
    "EmulatedDevice",
    under=stc_project,
    Name="Router 1",
    EnablePingResponse="TRUE",
    RouterId=stormwind_router_id,
)

stormwind_eth = stc_session.create(
    "EthIIIf",
    under=stormwind_device,
)

stormwind_ip = stc_session.create(
    "Ipv4If",
    under=stormwind_device,
    Address=stormwind_int_ip,
    Gateway=ironforge_int_ip,
    PrefixLength="24",
)

# Configure BGP parameters
bgp_router_config = stc_session.create(
    "BgpRouterConfig",
    under=stormwind_device,
    AsNum=stormwind_as,
    DutAsNum=ironforge_as,
    UseGatewayAsDut="TRUE",
)

bgp_ipv4_route_config = stc_session.create(
    "BgpIpv4RouteConfig",
    under=bgp_router_config,
    NextHop=stormwind_int_ip,
    AsPath=stormwind_as,
)

ipv4_network_block = (
    stc_session.get(bgp_ipv4_route_config, "children-Ipv4NetworkBlock")
).split(" ")[0]

stc_session.config(
    ipv4_network_block,
    StartIpList=generated_prefixes_start_ip,
    PrefixLength="24",
    NetworkCount=generated_bgp_routes,
)

bgp_route_gen_params = stc_session.create("BgpRouteGenParams", under=stc_project)

ipv4_route_gen_params = stc_session.create(
    "Ipv4RouteGenParams",
    under=bgp_route_gen_params,
    IpAddrStart=generated_prefixes_start_ip,
    PrefixLengthStart="24",
    PrefixLengthEnd="24",
    Count=generated_bgp_routes,
)

bgp_route_gen_route_attr_params = stc_session.create(
    "BgpRouteGenRouteAttrParams", under=ipv4_route_gen_params
)


stc_session.perform("ReservePortCommand", Location=port_location)
stc_session.perform("attachPorts")

stc_session.config(port3_handler, **{"AffiliationPort-sources": [stormwind_device]})

stc_session.config(stormwind_device, **{"TopLevelIf-targets": [stormwind_ip]})
stc_session.config(stormwind_device, **{"PrimaryIf-targets": [stormwind_ip]})

stc_session.config(stormwind_ip, **{"StackedOnEndpoint-targets": [stormwind_eth]})

stc_session.config(bgp_router_config, **{"UsesIf-targets": [stormwind_ip]})
stc_session.config(
    bgp_route_gen_params,
    **{"SelectedRouterRelation-targets": [stormwind_device]},
)

stc_session.apply()

print("Starting Stormwind router")
stc_session.perform("ArpNdStartCommand", HandleList=port3_handler)
stc_session.perform("DeviceStartCommand", DeviceList=stormwind_device)

TRAFFIC_GENERATION_TIME = 180
print(f"Waiting for {TRAFFIC_GENERATION_TIME} seconds")
time.sleep(TRAFFIC_GENERATION_TIME)

stc_session.perform("DeviceStopCommand", DeviceList=stormwind_device)

stc_session.perform("ReleasePortCommand", Location=port_location)
stc_session.perform("chassisDisconnectAll")
stc_session.perform("resetConfig", createnewtestsessionid=0)
stc_session.end_session()
