
    def sync_ru_dispatcher_files(self, files, voices):
        """Publish loose RU dispatcher voices and remove UTFs only after verification."""
        import hashlib
        import re
        voices=tuple(voices)
        if not voices or any(v not in ('dispatcher01','dispatcher02','dispatcher03') for v in voices):
            raise ValueError('Unexpected dispatcher migration')
        fixed={'AUDIO/voices_space_male.ini','AUDIO/voices_space_female.ini','MISSIONS/voice_properties.ini'}
        pattern=r'AUDIO/MOD/(?:'+ '|'.join(voices) + r')/(?:[a-zA-Z0-9_+\-]+\.wav|manifest\.json|archive/0x[0-9a-f]+_[0-9a-f]{12}\.wav)'
        for name in files:
            if name not in fixed and not re.fullmatch(pattern,name):raise ValueError('Unexpected dispatcher target: '+name)
            self.data_path(name)
        if not {'AUDIO/voices_space_male.ini','AUDIO/voices_space_female.ini'} <= files.keys():
            raise ValueError('Both voice registries are required')
        for voice in voices:
            manifest=json.loads(files[f'AUDIO/MOD/{voice}/manifest.json'])
            # Only playable recordings are required. Historical archive entries
            # are optional provenance, not inputs to subsequent compilations.
            for row in manifest['recordings'].values():
                target=row['file']
                raw=files.get(target)
                if raw is None:raw=self.data_path(target).read_bytes()
                if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Unverified audio: '+target)
            bank=self.data_path(f'AUDIO/{voice}.utf')
            if bank.exists() and hashlib.sha256(bank.read_bytes()).hexdigest()!=manifest['source_utf_sha256']:
                raise ValueError('UTF changed during compilation: '+voice)
        before={name:self.data_path(name).read_bytes() if self.data_path(name).exists() else None for name in files}
        archives={f'AUDIO/{v}.utf':self.data_path(f'AUDIO/{v}.utf').read_bytes() for v in voices if self.data_path(f'AUDIO/{v}.utf').exists()}
        touched=[];removed=[]
        try:
            # File payloads first, then manifests/INI. No bank is removed until
            # the complete replacement is on disk and verified byte-for-byte.
            for name,raw in sorted(files.items(),key=lambda item:not item[0].endswith('.wav')):
                if before[name]==raw:continue
                touched.append(name);self.sync_data_file(name,raw)
            for name,raw in files.items():
                if self.data_path(name).read_bytes()!=raw:raise IOError('Dispatcher verification failed: '+name)
            for name in archives:
                removed.append(name);self.remove_data_file(name)
                if self.data_path(name).exists():raise IOError('UTF remains active: '+name)
        except Exception:
            for name in removed:self.sync_data_file(name,archives[name])
            for name in reversed(touched):
                if before[name] is None:self.remove_data_file(name)
                else:self.sync_data_file(name,before[name])
            raise
