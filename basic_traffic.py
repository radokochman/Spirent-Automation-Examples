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


stc_session = stchttp.StcHttp(stc_server, port=port)
stc_session.new_session(
    user_name=user_name, session_name=session_name, kill_existing=True
)
stc_project = stc_session.create("project")

orgrimmar_device = stc_session.create(
    "EmulatedDevice", under=stc_project, EnablePingResponse="TRUE"
)
undercity_device = stc_session.create(
    "EmulatedDevice", under=stc_project, EnablePingResponse="TRUE"
)

orgrimmar_eth = stc_session.create("EthIIIf", under=orgrimmar_device)
undercity_eth = stc_session.create("EthIIIf", under=undercity_device)

orgrimmar_ip = stc_session.create(
    "Ipv4If",
    under=orgrimmar_device,
    Address="10.255.1.2",
    Gateway="10.255.1.1",
    PrefixLength="24",
)
undercity_ip = stc_session.create(
    "Ipv4If",
    under=undercity_device,
    Address="10.255.2.2",
    Gateway="10.255.2.1",
    PrefixLength="24",
)

stc_session.connect(spirent_box)

port_locations = ["//10.0.0.1/1/2", "//10.0.0.1/1/4"]
port_handlers = [
    stc_session.create("Port", under=stc_project, Location=port)
    for port in port_locations
]
port2_handler = port_handlers[0]
port4_handler = port_handlers[1]

stc_session.perform("ReservePortCommand", Location=port_locations)

stc_session.perform("attachPorts")

stream_block = stc_session.create("streamBlock", under=port4_handler)

stc_session.config(port4_handler, **{"AffiliationPort-sources": [orgrimmar_device]})
stc_session.config(port2_handler, **{"AffiliationPort-sources": [undercity_device]})

stc_session.config(orgrimmar_device, **{"TopLevelIf-targets": [orgrimmar_ip]})
stc_session.config(orgrimmar_device, **{"PrimaryIf-targets": [orgrimmar_ip]})

stc_session.config(undercity_device, **{"TopLevelIf-targets": [undercity_ip]})
stc_session.config(undercity_device, **{"PrimaryIf-targets": [undercity_ip]})

stc_session.config(
    orgrimmar_ip, attributes={"StackedOnEndpoint-targets": [orgrimmar_eth]}
)
stc_session.config(
    undercity_ip, attributes={"StackedOnEndpoint-targets": [undercity_eth]}
)

stc_session.config(stream_block, attributes={"SrcBinding-targets": [orgrimmar_ip]})
stc_session.config(stream_block, attributes={"DstBinding-targets": [undercity_ip]})

stc_session.apply()

stc_session.perform("ArpNdStartCommand", HandleList=port_handlers)
stc_session.perform("DevicesStartAllCommand")

print("Starting generator")
generator = stc_session.get(port4_handler, "children-Generator")
stc_session.perform("GeneratorStart", GeneratorList=generator)

TRAFFIC_GENERATION_TIME = 60
print(f"Waiting for {TRAFFIC_GENERATION_TIME} seconds")
time.sleep(TRAFFIC_GENERATION_TIME)

print("Stopping generator")
stc_session.perform("GeneratorStop", GeneratorList=generator)

stc_session.perform("DevicesStopAllCommand")

stc_session.perform("ReleasePortCommand", Location=port_locations)
stc_session.perform("chassisDisconnectAll")
stc_session.perform("resetConfig", createnewtestsessionid=0)
stc_session.end_session()
