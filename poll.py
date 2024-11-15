import urllib.request, json, os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import pickle
import sched

def poll_status( scheduler, url, auth_token ):

    scheduler.enter(20, 1, poll_status, (scheduler, url, auth_token))
    ltz = ZoneInfo('Europe/Stockholm')
    now = datetime.now(tz=ltz)

    try:
        req = urllib.request.Request(url, headers={'Auth-Token': auth_token})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())

        # print(json.dumps(data,indent=2))

        old = now - timedelta(days=2)

        if 'Timestamp' in data and type(data['Timestamp']) == str:
            local_tz = 'Europe/Stockholm'
            t = datetime.strptime(data['Timestamp'], '%Y-%m-%d %H:%M:%S').astimezone(ltz)
            data['Timestamp'] = t

        entries = []
        status_db_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.status.db')
        if os.path.exists(status_db_filename):
            with open(status_db_filename, 'rb') as f:
                entries = pickle.load(f)

        entries = [x for x in entries if x['Timestamp'] > old] + [data]

        with open(status_db_filename, 'wb') as f:
            pickle.dump(entries, f)

    except Exception as e:
        print(f'{now.isoformat()}: {e}')


auth_token = os.environ.get('INVERTER_AUTH_TOKEN', 'super secret auth token')
scrape_url = os.environ.get('INVERTER_SCRAPE_URL', 'my very secret url in my super secret domain.')

scheduler = sched.scheduler()
scheduler.enter(20, 1, poll_status, (scheduler,scrape_url,auth_token))
scheduler.run()
