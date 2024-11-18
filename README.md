# Airbleep

![161124_egarbage-aureline](https://github.com/user-attachments/assets/907a0894-725c-4be8-84e4-350e51019405)

Airbleep is a stupid but yet working python warper for airodump-ng that translate to OSC and MIDI notes all the signals coming from wifi clients nearby (i.e any wifi device that doesn’t act as an AP). It correlate signal strength to sound intensity, and gives every MAC address a unique sound. This is has been developed as an art project, but try to explore how to use sonification of data in a context of dense and not easily readable data landscape such as wifi devices coming in and out in a city center.

## Core Concept and Research

At the origin of the Airbleep project is the following question: How easy is it to detect someone’s smartphone passively, without messing with GSM/LTE? Ignoring GSM/LTE is mainly for legal and safety reasons, but also for technical reasons since it needs more advanced hardware than other wireless communication (by advanced I mean, less easily sourceable). This first question led to investigate what kind of signal a smartphone emit, and which one can easly picked up. Wifi has been chosen for it’s straight nature  and it ease of use through well documented tools such as the Aircrack-ng suite. This project is intended to be use for electronic music production/live, data visualization. Its main purpose is to make people realise how data are volatile, and all around us, and how this can have an impact on our private lives.

## Disclaimer

Airbleep shoul not be use without prior authorization, check the law in your country on monitoring wifi before using it. I am not responsible for any illegal use of this script.

## Behind the scene

Airbleep is developed on top of the Aircrack-ng suite, more specifically Airodump-ng. This has been a natural choice for two main reasons:

- Aircrack is well know, well documented and reliable wifi monitoring suite, mainly use in the cybersecurity field, it include all the necessary tools to investigate wifi traffic, from network adapter management to security analysis.
- complexity of developpement, this project is a proof of concept developped for a one time art installation.

Since I’m bad at coding, this script dumbly launch airodump-ng, and then pipe its output to be red as text by the script itself. This is highly inefficient, but meh, it works :)

### MIDI messages

It then hash the value of each BSSID (MAC address of client device detected) and modulo 128 it to get an integer between 0 and 127 which correspond to the note range of MIDI. It also remap the power value for each detected client to a 0-127 range that correspond to the note velocity in MIDI. This two data are then send to all available midi outs. MIDI messages are send as soon as a new client is detected or updated

### OSC messages

Unlike MIDI, OSC messages are much more litterals 3 OSC channel are send everytime:
- client: string containg client BSSID
- pwr: float singal power between 0-1
- probes: strring with probes for each station

OSC messages are send at the same time as MIDI messages

## Installation

- First you need a monitor mode capable wifi interface, it can be bought off ebay or alibaba for cheap. You also need a computer with Python ≥3.9
- Then you need to install airmon-ng and airodump-ng from the Aircrack-ng suite
    
    ```bash
    sudo apt install aircrack-ng
    ```
    
- Then download this repo:

    ```bash
    git clone https://github.com/e-garbage/airbleep/
    ```

- Install the dependencies through pip

    ```bash
    cd airbleep && pip install requirements.txt
    ```

### Usage

- First run airmon-ng to setup your wifi adaptor of choice to monitor mode
    
    ```bash
    sudo airmon-ng #run this command to see all the available wifi adaptors
    sudo arimon-ng start <your wifi adaptor name> #this will switch to monitor mode
    ```
    
- Then run the script
    
    ```bash
    sudo python3 airbleep.py -i wlan0mon
    ```
    

### Options

Airbleep offers 4 parameters:

- -ip: set the IP of the machine you want to send OSC messages to. By default it is set to [localhost](http://localhost) 127.0.0.1, this allow to loopback OSC messages on the same computer and make script communicate with another program such as Max4Live, PureData, TouchDesigner running locally.
- -p: set the port of the machine you want to send OSC messages to. By Default it is set to port 10000
- -i: name of the monitor interface, by default “wlan0mon”
- -h: display help

## Airbleep art installation, Geneva 2024

![161124_egarbage-pablo](https://github.com/user-attachments/assets/0494859b-a8b9-49ea-9429-e02f97f7e280)

Thanks to the Folnui collective, I was able to build, present and perform with a structure than integrated this script as its core. Made out of recycled materials exclusively (old pieces of wood, laying around screens and cables, and a repurposed 11years old laptop) this was the first public implementation of this sonification script. 

![161124_egarbage-joel_5](https://github.com/user-attachments/assets/23a542cc-2e26-406b-aff8-59d2f22d7b49)


The guys there also implemented an impressive light show as well as a huge mapping of a nearby building showing all the captured datas. 

![161124_egarbage-joel_7](https://github.com/user-attachments/assets/c8198b90-3a63-4d78-a2a7-351427c99227)

Finally I performed a 1h live improvised live set using almost exclusively this script to create melodies and texture in a techno genre. I sequenced myself all the other sounds and instruments. Before and after, people enjoyed the nicely dissonant sounds of wifi triggered synth since this is basically generative music ;)


All the pictures made by [Folnui](https://www.folnui.com/) 
Hit me up for any questions.
