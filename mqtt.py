import paho.mqtt.client as mqtt
import time
import json

# Set up your broker details (hostname, port, etc.)
mqtt_host = "192.168.1.10"
mqtt_port = 1884

#publish topics
pubtopic = "pub/input_tab/fw_output"

#subscribe topics
sub_car_power = "sub/input_tab/car_power"
sub_charging_state = "sub/input_tab/charging_state"
sub_object_detected = "sub/input_tab/object_detected"
sub_ventilated_seats = "sub/input_tab/ventilated_seats"
sub_sunroof = "sub/input_tab/sunroof"
sub_dust = "sub/input_tab/dust"
sub_snow = "sub/input_tab/snow"
sub_environment_temp = "sub/input_tab/environment_temp"
sub_manual_door_state = "sub/input_tab/manual_door_state"

#publish topic data dictionary
pub_data = {
  "speed": 0.0,
  "battery": 0.0,
  "door_lock": False,
  "estimated_range": 0.0
}

#loop_delay in seconds
LOOP_DELAY = 0.5
#time constant
TIME_RATE = 30               #time simulation rate 1s simulate to 30mins
MIN_IN_HOUR = 60
TOTAL_HOUR_OF_SIMULATION = LOOP_DELAY * TIME_RATE/MIN_IN_HOUR
#charging global variables
charge_state=False
battery_pc = 100
MAX_BAT_PC = 100
MIN_BAT_PC = 0
LOW_BAT_PC = 5
BAT_CHARGING_RATE = 1         #battery charging rate = 1 pc in 1min
ENVIRONMENT_BAT_DCHG =  0.001     #discharge battery due to 1 degree change in temp
environment_temp_val = 0
#power global variables
car_power_state=False
speed_val=0
SPEED_BAT_DCHG_RATE = 0.0001       #battery discharging pc due to 1km/h speed in 1h
#ventilated seats global variable
ventilated_seats_state = False
VEN_SEATS_BAT_DIS_RATE = 1      #battery percent change when ventilation seats on for 1h 
vent_seats_bat_dchg_rate = 0

#sunroof global variable
sunroof_state = False
SUNROOF_BAT_DIS_RATE = 1        #battery percent change
sunroof_bat_dchg_rate = 0

ACC_RATE = 1                    #for acc = 1 for 1h to speed change 1km/h
BREAK_RATE = 2                  #for break = 1 for 1h to speed change 2km/h
door_lock_state=False
DOOR_LOCK_THRESHOLD=10   
door_state = "close_unlock"        

acc_speed_list = [0, 10,20,30,40,50,60,70,80,90,100,110,120,180]
MIN_SPEED_VAL = 0
#reduce_speed =false
estimated_range_data=0
EST_RANGE_FULL_BATTERY = 200    #200km range on full battery

NORMAL_OBJECT_DISTANCE_THRESHOLD= 50  #50 meters
DUST_OBJECT_DISTANCE_THRESHOLD = 25   #25 meters
SNOW_OBJECT_DISTANCE_THRESHOLD = 30

object_detected_threshold = NORMAL_OBJECT_DISTANCE_THRESHOLD
object_detected = False
traffic_light_detected = False

dust_state = False
snow_state = False

#connection callback function
def on_connect(client, userdata, flags, reason_code, properties=None):
    print("Connected to MQTT broker!")
    client.subscribe("sub/input_tab/+")

#disconnect callback function
def on_disconnect(client, userdata, return_code):
    print("Disconnected to MQTT broker!")
    client.connect(mqtt_host, mqtt_port, keepalive=60)

#Message receive callback function
def on_message(client, userdata, message):
    try:
        json_string = message.payload.decode()                       #decoding the received message
        print(f"Received message: {json_string} on {message.topic}") #printing received message
        data = json.loads(json_string)                               #converting to json
    except Exception as e:
        print(f"Message Decoding error : {e}")
        return 0

    #function calls based on subscribe topics
    if message.topic == sub_car_power:
        on_car_power(data)
    elif message.topic == sub_charging_state:
        on_charging_state(data)
    elif message.topic == sub_object_detected:
        on_object_detected(data)
    elif message.topic == sub_ventilated_seats:
        on_ventilated_seats(data)
    elif message.topic == sub_sunroof:
        on_sunroof(data)
    elif message.topic == sub_dust:
        on_dust(data)
    elif message.topic == sub_snow:
        on_snow(data)
    elif message.topic == sub_environment_temp:
        on_environment_temp(data)
    elif message.topic == sub_manual_door_state:
        on_manual_door_state(data)

    '''json_data = json.dumps(pub_data)
    client.publish(pubtopic, json_data,qos=0)'''

#def on_publish(client, userdata, mid,reason_code, properties=None):
#    print("Published")

#subscription callback function
def on_subscribe(client, userdata, mid, qos, properties=None):
    print("Subscribed!")

#function will call when car power topic trigger
def on_car_power(data):
    global car_power_state
    try:
        car_power_state = data["car_power"]
        print(car_power_state)
    except Exception as e:
        print(f"on_car_power : {e}")

#function will call when charging state topic trigger
def on_charging_state(data):
    global charge_state
    try:
        charge_state = data["charging_state"]
        print(charge_state)
    except Exception as e:
        print(f"on_charging_state : {e}")

#function will call when object detected topic trigger
def on_object_detected(data):
    global object_detected
    if(car_power_state):
        try:
            obj_dist = data["distance"]
            obj_type = data["object_type"]
            print(obj_dist)
            print(obj_type)
            if(obj_type=="traffic_signal") :
                obj_traffic = data["traffic_signal"]
                print(obj_traffic)
                if(obj_traffic=="red" or obj_traffic=="yellow"):
                    if(obj_dist<object_detected_threshold):
                        traffic_light_detected = True
                if(obj_traffic=="green"):
                        traffic_light_detected = False
            elif(obj_type=="car" or obj_type=="pedestrian" ):
                if(obj_dist<object_detected_threshold):
                        object_detected = True
                
        except Exception as e:
            print(f"on_object_detected : {e}")

#function will call when ventilated seats topic trigger
def on_ventilated_seats(data):
    global ventilated_seats_state, vent_seats_bat_dchg_rate
    if(car_power_state):
        try:
            ventilated_seats_state = data["ventilated_seats"]
            print(ventilated_seats_state)
            if(ventilated_seats_state):
                vent_seats_bat_dchg_rate=VEN_SEATS_BAT_DIS_RATE
            else:
                vent_seats_bat_dchg_rate=0
        except Exception as e:
            print(f"on_ventilated_seats : {e}")

#function will call when sunroof topic trigger
def on_sunroof(data):
    global sunroof_state, sunroof_bat_dchg_rate
    if(car_power_state):
        try:
            sunroof_state = data["sunroof"]
            print(sunroof_state)
            if(sunroof_state):
                sunroof_bat_dchg_rate = SUNROOF_BAT_DIS_RATE
            else:
                sunroof_bat_dchg_rate = 0
        except Exception as e:
            print(f"on_sunroof : {e}")

#function will call when dust topic trigger
def on_dust(data):
    if(car_power_state):
        try:
            dust_state = data["dust"]
            print(dust_state)
            if(dust_state):
                object_detected_threshold = DUST_OBJECT_DISTANCE_THRESHOLD
            else:
                object_detected_threshold = NORMAL_OBJECT_DISTANCE_THRESHOLD
        except Exception as e:
            print(f"on_dust : {e}")

#function will call when snow topic trigger
def on_snow(data):
    if(car_power_state):
        try:
            snow_state = data["snow"]
            print(snow_state)
            if(snow_state):
                object_detected_threshold = SNOW_OBJECT_DISTANCE_THRESHOLD
            else:
                object_detected_threshold = NORMAL_OBJECT_DISTANCE_THRESHOLD
        except Exception as e:
            print(f"on_snow : {e}")

#function will call when environment temp topic trigger
def on_environment_temp(data):
    global environment_temp_val
    if(car_power_state):
        try:
            environment_temp_val=data["environment_temp"]
            print(environment_temp_val)
        except Exception as e:
            print(f"on_environment_temp : {e}")

#function will call when manual door state topic trigger            
def on_manual_door_state(data):
    global door_state
    if(car_power_state):
        try:
            door_state = data["manual_door_state"]
            print(door_state)
            
            if(door_state=="close_lock"):
                door_lock_state = True
            else:
                door_lock_state = False
    
        except Exception as e:
            print(f"on_manual_door_state : {e}")

#function to publish the data on publish topic
def on_request_publish():
    pub_data["speed"] = round(speed_val,2)
    pub_data["battery"] = round(battery_pc,2)
    pub_data["door_lock"] = door_lock_state
    pub_data["estimated_range"] = round(estimated_range_data,2)
    print("------------------------------------------------------")
    print(pub_data)
    
    json_data = json.dumps(pub_data)
    client.publish(pubtopic, json_data,qos=0)

#function to simulate charging    
def battery_charge_simulation():
    global battery_pc, car_power_state
    if(charge_state):
        battery_pc = battery_pc + BAT_CHARGING_RATE*TOTAL_HOUR_OF_SIMULATION*MIN_IN_HOUR
        if battery_pc >=MAX_BAT_PC:
            battery_pc = MAX_BAT_PC
    else:
        
        #print((vent_seats_bat_dchg_rate+sunroof_bat_dchg_rate)*TOTAL_HOUR_OF_SIMULATION)
        battery_pc = battery_pc - (speed_val*SPEED_BAT_DCHG_RATE)*TOTAL_HOUR_OF_SIMULATION-(vent_seats_bat_dchg_rate+sunroof_bat_dchg_rate + environment_temp_val*ENVIRONMENT_BAT_DCHG)*TOTAL_HOUR_OF_SIMULATION
        if battery_pc <=MIN_BAT_PC:
            battery_pc = MIN_BAT_PC

#function to simulate speed depending on break and acc applied
def speed_simulation(break_data,acc_data):
    global car_power_state, speed_val
    max_speed = acc_speed_list[int(acc_data)]

    if(speed_val<max_speed):
        speed_val = speed_val + (acc_data*ACC_RATE)*TOTAL_HOUR_OF_SIMULATION
    else:
        speed_val = speed_val - (acc_data*ACC_RATE)*TOTAL_HOUR_OF_SIMULATION 
        if(speed_val<max_speed):
            speed_val = max_speed
    
    speed_val = speed_val - break_data*BREAK_RATE*TOTAL_HOUR_OF_SIMULATION 
    
    if(speed_val<MIN_SPEED_VAL):  
        speed_val = MIN_SPEED_VAL
    if(battery_pc<LOW_BAT_PC):  
        speed_val=0
    if(door_state=="open"):
        # print(speed_val)              
        speed_val=0 
    elif(charge_state):
        speed_val = MIN_SPEED_VAL
        
    
    #print(speed_val)    
    
def door_lock_simulation():
    global car_power_state, speed_val, door_lock_state
    if(car_power_state):
        if(speed_val>DOOR_LOCK_THRESHOLD):
            door_lock_state = True
        else:
            door_lock_state = False
    else:
        door_lock_state = False

def estimated_range_simulation():
    global battery_pc,estimated_range_data
    
    estimated_range_data = battery_pc * EST_RANGE_FULL_BATTERY/100
                    
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect
client.on_subscribe = on_subscribe
#client.on_publish = on_publish

client.connect(mqtt_host, mqtt_port, keepalive=60)

# Start the MQTT loop
client.loop_start()
counter = 0

while True: 
    
    if(charge_state or car_power_state):
#################################for simulation actual CAN code is needed#######################
        battery_charge_simulation()
        # if(counter <= 20):
        speed_simulation(0,13)
        # elif(counter > 20 and counter <= 40):
            # speed_simulation(0,8)
        # elif(counter > 40 and counter <= 60):
            # speed_simulation(0,13)
        
        # else:
            # counter=0
        
        if(car_power_state):
            counter = counter+1
######################################################################################                    
        door_lock_simulation()
        estimated_range_simulation()
        
        if(traffic_light_detected):
            #CAN call is needed to send information about object to stm32 
            while(speed_val):
                speed_simulation(3,0)
                on_request_publish()
                time.sleep(LOOP_DELAY)
            counter=0 
        elif(object_detected): 
            #CAN call is needed to send information about object to stm32 
            while(speed_val):
                speed_simulation(3,0)
                on_request_publish()
                time.sleep(LOOP_DELAY)
            time.sleep(5)
            object_detected = False
            counter=0 
        else:
            on_request_publish()

    elif(not car_power_state and speed_val > 0):
        speed_simulation(17,0)
        estimated_range_simulation()
        battery_charge_simulation()
        on_request_publish()

    time.sleep(LOOP_DELAY)