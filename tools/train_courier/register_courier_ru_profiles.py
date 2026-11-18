"""Add the missing RU reference samples to the running VoiceStudio library."""
import hashlib
import json
from pathlib import Path
from generate_courier_ru import OUT, save, sha
from generate_evacuation_audio import Recorder


def main():
    refs = json.loads((OUT/'references/manifest.json').read_text(encoding='utf-8'))
    cache_path = OUT/'profiles.json'
    cache = json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {}
    with Recorder._client() as client:
        response = client.get('/profiles')
        response.raise_for_status()
        profiles = response.json()
        profiles = profiles if isinstance(profiles,list) else profiles.get('profiles',profiles.get('items',[]))
        for name, record in refs.items():
            source = Path(record['path'])
            assert sha(source)==record['sha256']
            key = name+'|ru|'+hashlib.sha1(source.read_bytes()).hexdigest()
            title = 'nl-'+name+'-ru'
            if key in cache:
                check = client.get('/profiles/'+cache[key])
                if check.status_code==200:
                    print('Already registered:',title,cache[key])
                    continue
            existing = [p for p in profiles if p['name']==title]
            assert not existing, 'An existing sample needs comparison before reuse: '+title
            with source.open('rb') as stream:
                response = client.post('/profiles',data=dict(name=title,kind='clone',language='ru',ref_text=record['text']),
                    files={'ref_audio':(source.name,stream,'audio/wav')})
            response.raise_for_status()
            cache[key] = response.json()['id']
            save(cache_path,cache)
            print('Added:',title,cache[key],flush=True)


if __name__=='__main__':
    main()
