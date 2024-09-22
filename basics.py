from stcrestclient import stchttp

# Connection variables
stc_server = "10.0.0.1"
port = 8888

# Session variables
user_name = "radokochman"
session_name = "Script"
session_id = f"{session_name} - {user_name}"


stc_session = stchttp.StcHttp(stc_server, port=port)

system_info = stc_session.system_info()
print(f"System info: {system_info}")

sessions = stc_session.sessions()
print(f"List of sessions before createting a new one: {sessions}")

try:
    print(f"Creating new session: {session_id}")
    stc_session.new_session(user_name=user_name, session_name=session_name)
    print("Created a new session")
except RuntimeError:
    print("Session already exists, joining to it")
    stc_session.join_session(session_id)
    print(f"Joined session: {session_id}")


sessions = stc_session.sessions()
print(f"List of sessions after creating/joining: {sessions}")

stc_project = stc_session.create("project")
print(f"Created a new project: {stc_project}")

print("Ending session")
stc_session.end_session()
