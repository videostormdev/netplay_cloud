NetPlay Cloud Python process
-----------------------------------------

runNetPlay_controller.py :   This process acts as a controller for a NetPlay Cloud attached device

usage   ./runNetPlay_controller.py email password uuid

     uuid:  UUID of the device you will control.  UUIDs attached to your NetPlay Cloud account can be seen in your SplashTiles account linking page.  https://splash-tiles.com/console/account_linking.php


You must run with STDIN piped to another program (or modify the code).  Reads from piped STDIN the netplay protocol commands to send to the TX node of the controlled device.  Will also read the RX node responses and write these to STDOUT. Remember NetPlay protocol uses \r and the command delimiter (not \n).


This program will ERROR OUT if the NetPlay Cloud device node for the give UUID does not exist.



runNetPlay_device.py : This process connects a device (to be controlled) to NetPlay Cloud

usage:  ./runNetPlay_device.py email password uuid

     uuid:  The unique identifier of this device (usually based on mac address, ie pythondev-001122334455)


You must run with STDIN and STDOUT piped to another program (or modify the code).  Reads the TX node for this UUID and sends it to STDOUT.  Attached program should process the NetPlay Protocol and send the response back via STDIN (which this process writes back to the RX node).  Remember NetPlay protocol uses \r and the command delimiter (not \n).

This program will CREATE the NetPlay Cloud device database node for this UUID if it does not already exist.



IMPORTANT!

The API keys contained in this code allow you to connect to the NetPlay Cloud Firebase service.
This service shall only be used per the terms defined at https://www.video-storm.com/cloudappend.php

Do not use the NetPlay Cloud service for other purposes.  You will be liable for all cloud usage charges related to unautherized use.

If you have a different use case, just setup your own Firebase realtime database.  Google offers a free use tier for this service, so no reason not to do the right thing.  Thanks!
