# ohjaus
ohjaus is a Controlling system for your entire Smart Home.

## design principles
It started as a bunch of scripts run from Cron.
The end goal is to make meaningful decisions about controlling the loads inside the house.
If there's plenty of energy from the photovoltaics or the spot price for electicity is low, act on it.
The rulesets are simple logic so no machine learning / training is involved. Or needed. Feel free to implement.

## usage
Can be run from a suitable python virtual environment.

"python3 ohjaus.py" will run one cycle of the logic and store state in /tmp filesystem for later perusal.

## equipment
It's difficult to be device/protocol agnostic, so here's the equipment that can get you started:

- Raspberry pi (any version)
- Raspbee HAT (zigbee) from Dresden Elektronik
- OSRAM Smart+ smart zigbee sockets (to plug your water boiler, and other loads)
- Temperature sensors (zigbee) (for getting the real time water temperature info)
- some solar panels + inverters (I have Envertec inverters)
- a Tesla or other EV that offers public API over the internet
- 
