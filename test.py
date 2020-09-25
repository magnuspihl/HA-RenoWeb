# coding=utf-8
import sensor

conf = {
	#sensor.CONF_NAME: 'Garbage',
	sensor.CONF_DOMAIN: '2020solrod-swdk.renoweb.dk',
	sensor.CONF_ADDRESS: 'Maglekærvej 42'
}
def debug_entities(entities, whatever = True):
	for e in entities:
		e.update()
		print(e.name)
		print(e.icon)
		print(e.state)
		print(e.device_state_attributes)

sensor.setup_platform(None, conf, debug_entities)