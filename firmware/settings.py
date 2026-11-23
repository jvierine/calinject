"""Explicit, validated, atomic persistent settings; no automatic flash writes."""
import json,os
DEFAULTS=dict(width_us=100,mode='burst',atten_code=63,manual=False,servo=True,
              slope=.0806,dac=1862,ref10=False,refpps=False)
def validate(values):
    if not isinstance(values,dict) or set(values)!=set(DEFAULTS):raise ValueError('settings schema')
    for key in ['manual','servo','ref10','refpps']:
        if not isinstance(values[key],bool):raise ValueError(key+' must be boolean')
    for key,lo,hi in [('width_us',1,900000),('atten_code',0,63),('dac',700,3000)]:
        if type(values[key]) is not int or not lo<=values[key]<=hi:raise ValueError('invalid '+key)
    if values['mode'] not in ['burst','mute','continuous']:raise ValueError('invalid mode')
    if not isinstance(values['slope'],(int,float)) or not .01<values['slope']<.5:raise ValueError('invalid slope')
    return dict(values)
def load(path='settings.json'):
    try:
        with open(path) as f:return validate(json.load(f)),True
    except (OSError,ValueError,TypeError):return dict(DEFAULTS),False
def save(values,path='settings.json'):
    values=validate(values)
    with open(path+'.tmp','w') as f:json.dump(values,f)
    if hasattr(os,'sync'):os.sync()
    os.rename(path+'.tmp',path)
    if hasattr(os,'sync'):os.sync()
