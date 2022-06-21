from datetime import datetime, timedelta
import pytz
import json

def fitbit_activity_parser(raw_event, personicle_user_id):
    """
    Formats an activity received from FitbitAPI to personicle event schema
    """
    new_event_record = {}
    epoch = datetime.utcfromtimestamp(0).replace(tzinfo=None)
    new_event_record['individual_id'] = personicle_user_id
    # timestamp format 2021-11-25T09:27:30.000-08:00
    new_event_record['start_time'] = int((datetime.strptime(raw_event['startTime'], "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(pytz.utc).replace(tzinfo=None)-epoch).total_seconds()*1000)
    duration = timedelta(seconds=raw_event['originalDuration']/1000)
    new_event_record['end_time'] = int(new_event_record['start_time'] + duration.total_seconds()*1000)

    new_event_record['event_name'] = "activity"
    new_event_record['source'] = 'fitbit'
    new_event_record['parameters'] = json.dumps({
        "duration": duration.total_seconds(),
        "caloriesBurned": raw_event['calories'],
        'activityName': raw_event['activityName'],
        'distance': raw_event['distance'],
        'distanceUnit': raw_event['distanceUnit'],
        "activityLevel": raw_event['activityLevel']
    })
    return new_event_record
    
def fitbit_sleep_parser(raw_event, personicle_user_id):
    """
    Parse sleep event data from fitbit REST API

    The sleep event may also include sleep stages information
    need to parse that information as sleep.stages events that are sub-events of the coresponding sleep event
    """
    new_event_record = {}
    epoch = datetime.utcfromtimestamp(0).replace(tzinfo=None)
    new_event_record['individual_id'] = personicle_user_id
    # timestamp format 2021-11-25T09:27:30.000-08:00
    # new_event_record['start_time'] = int((datetime.strptime(raw_event['startTime'], "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(pytz.utc).replace(tzinfo=None)-epoch).total_seconds()*1000)
    new_event_record['start_time'] = int((datetime.strptime(raw_event['startTime'], "%Y-%m-%dT%H:%M:%S.%f").astimezone(pytz.utc).replace(tzinfo=None)-epoch).total_seconds()*1000)
    duration = timedelta(seconds=raw_event['duration']/1000)
    new_event_record['end_time'] = int(new_event_record['start_time'] + duration.total_seconds()*1000)

    new_event_record['event_name'] = "sleep"
    new_event_record['source'] = 'fitbit'
    new_event_record['parameters'] = json.dumps({
        "duration": duration.total_seconds(),
        "efficiency": raw_event['efficiency'],
        'minutes_asleep': raw_event['minutesAsleep'],
        'minutes_awake': raw_event['minutesAwake'],
        'sleep_latency': raw_event['minutesToFallAsleep'],
        "time_in_bed": raw_event['timeInBed'],
        "summary": raw_event.get('levels', {'summary': None}).get('summary', None)
    })

    # parse sleep stages information as separate events and send to event hub
    sleep_stages_events = fitbit_sleep_stages_parser(raw_event.get('levels', {'data': None}).get('data', None), personicle_user_id)
    if sleep_stages_events and len(sleep_stages_events) > 0:
        new_events = [new_event_record] + sleep_stages_events
        return new_events
    else:
        return new_event_record
    
def fitbit_sleep_stages_parser(raw_events, personicle_user_id):
    epoch = datetime.utcfromtimestamp(0).replace(tzinfo=None)
    if raw_events is None:
        return []
    formatted_events = []
    for stage_event in raw_events:
        # print(stage_event)
        new_stage_event = {}
        new_stage_event['individual_id'] = personicle_user_id
        new_stage_event['start_time'] = int((datetime.strptime(stage_event['dateTime'], "%Y-%m-%dT%H:%M:%S.%f").astimezone(pytz.utc).replace(tzinfo=None)-epoch).total_seconds()*1000)
        new_stage_event['end_time'] = new_stage_event['start_time'] + stage_event['seconds']*1000
        new_stage_event['event_name'] = "sleep.stages.{}".format(stage_event['level'])
        new_stage_event['source'] = "fitbit"
        new_stage_event['parameters'] = json.dumps({
            'duration': stage_event['seconds'],
            'sleep_level': stage_event['level']
        })
        formatted_events.append(new_stage_event)
    return formatted_events


def format_heartrate(raw_record, personicle_user_id = 'p01'):
    new_record = {}
    epoch = datetime.utcfromtimestamp(0)
    new_record['individual_id'] = personicle_user_id
    new_record['timestamp'] = (datetime.strptime(raw_record['dateTime'], "%Y-%m-%d %H:%M:%S") - epoch).total_seconds()*1000
    new_record['stream'] = 'heartrate'
    new_record['value'] = raw_record['value']['bpm']
    new_record['unit'] = 'bpm'
    new_record['confidence'] = raw_record['value']['confidence']

    return new_record