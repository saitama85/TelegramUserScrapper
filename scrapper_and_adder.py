
import sys
import csv
import traceback
import time
import random
import json

from telethon.sync import TelegramClient #Client Module to Login

from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser, InputPeerChat

from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, UserAlreadyParticipantError


from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.functions.messages import AddChatUserRequest


credential_file = "credentials.json" #Relative Path of File which consists Telegram Credentials(api_id, api_hash, phone)

start_index = 0
continue_script = False

if len(sys.argv) == 5:
    g_index_scrapper = sys.argv[1]
    g_index_adder = sys.argv[2]
    mode = sys.argv[3]
    start_index = sys.argv[4]
    continue_script = True

#Login & Verification Code
try:
    credentials = json.load(open(credential_file, 'r'))
except:
    print("credentials.json File not present in the directory")
    exit()

try:
    client = TelegramClient(credentials['phone'], credentials['api_id'], credentials['api_hash'])
    client.connect()
except:
    print("Could not create Telegram Client, Please check your Credentials in credentials.json file")
    exit()


if not client.is_user_authorized():
    client.send_code_request(credentials['phone'])
    client.sign_in(credentials['phone'], input('Enter  veryfication code: '))

#Chat parameters
chats = []
last_date = None
chunk_size = 200 # No of latest chats to load
groups = []

try:
    result = client(GetDialogsRequest(
        offset_date=last_date,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=chunk_size,
        hash=0
    ))
    chats.extend(result.chats)
except:
    print("Unable to gather chats from server. Please Check Chat parameters.")
    exit()

for chat in chats:
    try:
        groups.append(chat)
    except:
        continue

if len(groups) == 0:
    print("No Groups or Channels found.")
    exit()

print('Available Groups and Channels:')
i=1
for g in groups:
    print(str(i) + '- ' + g.title)
    i+=1

#User Inputs
if not continue_script:
    g_index_scrapper = input("Enter the index of Group/Channel to SCRAPE users from: ")
    target_group_scrapper = groups[int(g_index_scrapper)-1]

    g_index_adder = input("Enter the index of Group/Channel to ADD users to: ")
    target_group_adder = groups[int(g_index_adder)-1]

    mode = int(input("Enter 1 to add by username or 2 to add by ID: "))

if(mode not in [1,2]):
    sys.exit("Invalid Mode Selected. Please Try Again.")

#Fetching participants from server
all_participants = []
print('Fetching Members...')

try:
    all_participants = client.get_participants(target_group_scrapper, aggressive=True)
except: 
    print("Unable to fetch participants of", target_group_scrapper)
    exit()

if len(all_participants) == 0:
    print("No user found in", target_group_scrapper + '.', "Please check the group.")
    exit()

try:
    target_group_entity_adder = InputPeerChannel(target_group_adder.id, target_group_adder.access_hash)
    isChannel = True
except:
    target_group_entity_adder = InputPeerChat(target_group_adder.id)
    isChannel = False

n = 0
user_added_count = 0



for i in range(start_index,len(all_participants)):
    user = all_participants[i]
    n += 1
    if n % 50 == 0:
        time.sleep(900)

    try:
        print("Adding {}".format(user.id))
        if mode == 1:
            try:
                if user.username != None:
                    user_to_add = client.get_input_entity(user.username)
            except: 
                continue
            
        elif mode == 2:
            user_to_add = InputPeerUser(user.id, user.access_hash)
        
        if isChannel:
            client(InviteToChannelRequest(target_group_entity_adder, [user_to_add]))
        else:
            client(AddChatUserRequest(target_group_adder.id, user_to_add,fwd_limit=50))

        user_added_count += 1
        wait_time = random.randrange(60, 180)
        print("Waiting for",wait_time, "Seconds...")
        time.sleep(wait_time)
    except PeerFloodError:
        print("Getting Flood Error from telegram. Script is stopping now. Please try again after some time.")
        print("Run the following command after few hours to contiune where you left off:")
        print("python3 scrapper_and_adder.py", g_index_scrapper, g_index_adder, mode, i)
        sys.exit()
    except UserPrivacyRestrictedError:
        print("The user's privacy settings do not allow you to do this. Skipping.")
    except UserAlreadyParticipantError:
        continue
    except:
        traceback.print_exc()
        print("Unexpected Error")
        continue

print("Added:", user_added_count, "users to the group")
