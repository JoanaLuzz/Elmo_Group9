# Elmo

<img src="elmo.jpg" alt="drawing" height="250"/>


## What is Elmo?

Elmo is a robot designed by the portuguese start-up, IDMind, for a variety of applications, including educational entertainment (Edutainment), human-robot interaction (HRI), research, and commercial uses.

### Elmo hardware
Elmo components are:
 - 1 Power button 
 - 1 Ethernet port
 - 1 Microphone 
 - 2 Speakers
 - 1 13x13 Led Matrix
 - 5 Capacitive touch sensors (1 in the chest, 4 in the head)
 - 2 servo motors for head movement (pan and tilt)
 - 1 Touchscreen (face)
 - 1 RGB Camera
 - 1 Battery
 - Raspberry PI 4, running Raspberry PI OS Bullseye 
> [!CAUTION]
> All equipment underwent thorough testing and verification prior to its availability to students. Kindly exercise caution and ensure the return of each item enclosed in the box in the **same condition** as it was borrowed.
> Elmo is a fragile robot so ***be very careful*** with its neck, don't force the motors, and don't shack/move it violently.

## What you need to use Elmo?

- 1 Elmo
- 1 Charger
- 1 Router
- 1 or 2 Networking cable

## How to quickly start with Elmo?

### First you must configure the set-up

1. Connect Elmo with a networking cable to the router
    
>[!NOTE]
> If you need to be connected to the internet, connect the router to a ethernet socket with a networking cable <br> - On Lab 0 no ethernet sockets are available, so during lab classes the router will be supplied with Ethernet by the professor computer, but if you come to the lab before hours one of your team members must be the one sharing the ethernet connection throughout their computer - 

2. Connect you computer to the router network

3. Turn on the robot by pressing the button on its back for a few seconds.

4. Assure that you are using a python version between 3.8 and 3.11 or create your virtual environment with one of those.

5. Create a virtual environment.
> [!WARNING]
> It is good practice to create a virtual environment for each of your projects! 

6. Download the 3 scripts available into the same folder:
    - [find_elmo_ip.py](find_elmo_ip.py) - Python script that finds the Elmo ip on the network
    - [ElmoV2API.py](ElmoV2API.py) – Python class that  sends REST requests to the robot
    - [elmo_test.py](elmo_test.py) - Python script that shows how to use the ElmoV2API to connect and use Elmo

### Find the robot ip

To find elmo ip on the network run the small [script provided](find_elmo_ip.py)
```
python find_elmo_ip.py
```

### Run the [sample code](elmo_test.py)
```
python elmo_test.py <elmo_ip>
```

> [!IMPORTANT]
> Read the [ElmoV2API](ElmoV2API.py) class, has in there you can see which requests you can make to the robot. This requests are not limited as you can add more once you explored the code that Elmo is running. You can learn more about this on [the last section of this guide](#connect-with-elmo-via-ssh-to-discover-and-improve-its-code)


## How to add images, icons, sounds and videos to Elmo

Elmo can display images and videos on it's screen, display icons on its led matrix, and play sounds. But to do that you must copy those files to the correct directories into the Elmo Raspberry pi. So, then, from your code running in your computer, you just have to request to display/play the file that you added.

### Images
You can add all types of images, even gifs. To add your image you must run from your terminal:
```
scp -r /path/to/your/image idmind@<elmo_ip>:/home/idmind/elmo-v2/src/static/images
```

### Videos
To add your video you must run from your terminal:
```
scp -r /path/to/your/video idmind@<elmo_ip>:/home/idmind/elmo-v2/src/static/videos
```

### Sounds
To add your sounds you must run from your terminal:
```
scp -r /path/to/your/sound idmind@<elmo_ip>:/home/idmind/elmo-v2/src/static/sounds
```

### Icons
You can add images, even gifs, with the condition that they have 13x13 pixels only. To add your icon you must run from your terminal:
```
scp -r /path/to/your/icon idmind@<elmo_ip>:/home/idmind/elmo-v2/src/static/icons
```


## Connect with Elmo via SSH to discover and improve its code

To connect with Elmo via ssh, you have to run in your terminal:
```
ssh idmind@<elmo_ip>
```
The password is: **asdf**

> [!TIP]
> Explore the different drives that Elmo has and what they can do! (You can also do this on the [IDMind Elmo github](https://github.com/idmind-robotics/elmo-v2))<br>
> Also, explore the robot_api.py file to see what behaviors are available, and considering what each driver can do, implement your own.



