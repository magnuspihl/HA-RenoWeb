import requests, json, re, datetime
from homeassistant.helpers.entity import Entity

ATTR_NEXT_DATE = 'next_date'
ATTR_DAYS = 'days'
ATTR_FOOD_WASTE = 'food/waste' #mad-/restaffald
ATTR_PAPER_GLASS_CANS = 'paper/glass/cans' #papir og glas/dåser
ATTR_HAZARDOUS = 'hazardous' #miljøkasse
ATTR_PLASTICS = 'plastics' #plast
ATTR_CARDBOARD = 'cardboard' #pap
ATTR_LARGE = 'large' #storskrald
ATTR_GARDEN = 'garden' #haveaffald

CONF_NAME = "name"
CONF_DOMAIN = "domain"
CONF_ADDRESS = "address"

DEFAULT_NAME = "Garbage"

"""
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
	{
		vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
		vol.Required(CONF_DOMAIN): cv.string,
		vol.Required(CONF_ADDRESS): cv.string,
	}
)
"""
def setup_platform(hass, config, add_entities, discovery_info=None):
	"""Set up the SEAS-NVE sensor."""
	if (CONF_NAME in config):
		name = config[CONF_NAME]
	else:
		name = DEFAULT_NAME
	domain = config[CONF_DOMAIN]
	address = config[CONF_ADDRESS]
	
	data = RenoWebData(domain, address)
	add_entities([
		RenoWebSensor(data, name, ATTR_FOOD_WASTE, 'mdi:delete'),
		RenoWebSensor(data, name, ATTR_PAPER_GLASS_CANS, 'mdi:bottle-wine'),
		RenoWebSensor(data, name, ATTR_HAZARDOUS, 'mdi:biohazard'),
		RenoWebSensor(data, name, ATTR_PLASTICS, 'mdi:toy-brick'),
		RenoWebSensor(data, name, ATTR_CARDBOARD, 'mdi:archive'),
		RenoWebSensor(data, name, ATTR_LARGE, 'mdi:sofa'),
		RenoWebSensor(data, name, ATTR_GARDEN, 'mdi:leaf')
		], True)

class RenoWebSensor(Entity):
	"""Implementation of RenoWeb sensor"""
	
	def __init__(self, data, namePrefix, name, icon):
		self.data = data
		self._namePrefix = namePrefix
		self._name = name
		self._icon = icon
		self._info = self._state = None

	@property
	def name(self):
		"""Returns the name of the sensor."""
		return self._namePrefix + ' ' + self._name
	
	@property
	def state(self):
		"""Returns the state of the sensor."""
		return self._state
	
	@property
	def device_state_attributes(self):
		"""Returns the state attributes."""
		if not self._info:
			return {}
		
		nextDate = self._info[self._name]
		today = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
		delta = nextDate - today
		return {
			ATTR_NEXT_DATE: nextDate.astimezone(),
			ATTR_DAYS: delta.days
		}
	
	@property
	def unit_of_measurement(self):
		"""Return the unit this state is expressed in."""
		return ""
	
	@property
	def icon(self):
		"""Icon to use in the frontend, if any."""
		return self._icon
	
	def update(self):
		"""Get the latest data from the API and update the states."""
		self.data.update()
		self._info = self.data.info
		
		if not self._info:
			self._state = None
		else:
			try:
				self._state = self._info[self._name]
			except TypeError:
				pass

class RenoWebData:
	def __init__(self, domain, address):
		"""Initialize the data object."""
		self.domain = domain
		self.address = address
		self.adrid = None

	def getDate(self, data, name, description):
		for i in data:
			if (name is None or i['name'] == name) and (description is None or i['description'] == description):
				return i['date']
		return None

	def update(self):
		api = RenoWebApi(self.domain)
		if (self.adrid is None):
			self.adrid = api.getAddressId(self.address)
		material = api.getMaterial(self.adrid)
		self.info = {
			ATTR_FOOD_WASTE: self.getDate(material, 'Mad/Rest', None), #mad-/restaffald
			ATTR_PAPER_GLASS_CANS: self.getDate(material, 'papir og glas/dåser', '240 l 2-delt papir/glas-dåser en-familie (1 stk.)'), #papir og glas/dåser
			ATTR_HAZARDOUS: self.getDate(material, None, 'Miljøkasse (1 stk.)'), #miljøkasse
			ATTR_PLASTICS: self.getDate(material, 'Plast', None), #plast
			ATTR_CARDBOARD: self.getDate(material, 'Pap', None), #pap
			ATTR_LARGE: self.getDate(material, 'Storskrald', None), #storskrald
			ATTR_GARDEN: self.getDate(material, 'Haveaffald', None) #haveaffald
		}

class RenoWebApi:
	def __init__(self, host):
		global base_url
		base_url = 'https://' + host + '/Legacy/JService.asmx'
	
	def getAddressId(self, address):
		resp = requests.post(base_url + '/Adresse_SearchByString', json={'searchterm': address, 'addresswithmateriel': 0})
		respJson = resp.json()
		raw = json.loads(respJson['d'])
		l = raw['list']
		for i in l:
			return i['value']

	def getMaterial(self, addressId):
		resp = requests.post(base_url + '/GetAffaldsplanMateriel_mitAffald', json={'common': False, 'adrid': addressId})
		respJson = resp.json()
		raw = json.loads(respJson['d'])
		l = raw['list']
		result = []
		for i in l:
			x = re.search('[0-9]{2,2}-[0-9]{2,2}-[0-9]{4,4}', i['toemningsdato'])
			date = datetime.datetime.strptime(x.group(), '%d-%m-%Y')
			result.append({
				'name': i['ordningnavn'],
				'description': i['materielnavn'],
				'date': date,
				'formattedDate': i['toemningsdato']
			})
		return result