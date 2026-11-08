
    # BEGIN RPG AUDIO OUTPUT
    def rpg_bin_path(self, name):
        if name not in ('freelancer.ini', 'freelan_en_port.ini'):
            raise ValueError('Unexpected RPG audio launch configuration')
        root = self.get_root().resolve()
        path = (root / 'bin' / name).resolve()
        if not path.is_relative_to(root / 'bin'):
            raise ValueError('RPG launch configuration escaped bin')
        return path

    def sync_rpg_bin_file(self, name, content):
        path = self.rpg_bin_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def sync_rpg_audio(self, group, files, configs, backup_root):
        """One group's audio transaction. All DATA writes and rollback stay here."""
        import re
        if not re.fullmatch(r'rm[0-9]{4}', group):
            raise ValueError('Invalid RPG audio group')
        for relative in files:
            wav = re.fullmatch(r'AUDIO/(MOD|MOD_ENG)/RPG/' + group + '/' + group +
                               r'_frag[0-9]{4}_l001_(vendor|player)\.wav', relative)
            if not wav and relative not in (f'AUDIO/RPG/{group}.json', f'AUDIO/RPG/{group}_sounds.ini'):
                raise ValueError('Unexpected RPG audio target: ' + relative)
            self.data_path(relative)
        for name in configs:
            self.rpg_bin_path(name)
        self._sync_rpg_files(group, files, configs, backup_root)

    def sync_rpg_scenes(self, group, files, backup_root):
        import re
        if not re.fullmatch(r'rm[0-9]{4}', group):
            raise ValueError('Invalid RPG scene group')
        for relative in files:
            pattern = (r'SCRIPTS/RPG/' + group + r'/(ru|en)/(' + group +
                       r'_frag[0-9]{4}\.thn|manifest\.json|subtitles\.xml)')
            gesture = r'SCRIPTS/RPG/' + group + r'/gestures/(vendor|player)_0[1-8]\.thn'
            if not re.fullmatch(pattern, relative) and not re.fullmatch(gesture, relative):
                raise ValueError('Unexpected RPG scene target: ' + relative)
            self.data_path(relative)
        self._sync_rpg_files(group, files, {}, backup_root)

    def _sync_rpg_files(self, group, files, configs, backup_root):
        backup_root = pathlib.Path(backup_root).resolve()
        if backup_root == self.get_root().resolve() or backup_root.is_relative_to(self.data_path('AUDIO').parent):
            raise ValueError('Backup must be outside game DATA')
        backup = DataFolder(root=backup_root)
        before = {name: self.data_path(name).read_bytes() if self.data_path(name).exists() else None
                  for name in files}
        before_configs = {name: self.rpg_bin_path(name).read_bytes() for name in configs}
        changed = {name: content for name, content in files.items() if before[name] != content}
        changed_configs = {name: content for name, content in configs.items() if before_configs[name] != content}
        for name in changed:
            if before[name] is not None:
                backup.sync_data_file(name, before[name])
        for name in changed_configs:
            backup.sync_rpg_bin_file(name, before_configs[name])
        backup_root.mkdir(parents=True, exist_ok=True)
        (backup_root / 'transaction.json').write_text(json.dumps({
            'group': group, 'destination': str(self.get_root()),
            'data_files': {name: before[name] is not None for name in changed},
            'bin_files': list(changed_configs)}, indent=2), encoding='utf-8')
        touched, touched_configs = [], []
        try:
            for name, content in changed.items():
                touched.append(name)
                self.sync_data_file(name, content)
            for name, content in changed_configs.items():
                touched_configs.append(name)
                self.sync_rpg_bin_file(name, content)
        except Exception:
            for name in reversed(touched_configs):
                self.sync_rpg_bin_file(name, before_configs[name])
            for name in reversed(touched):
                if before[name] is None:
                    self.remove_data_file(name)
                else:
                    self.sync_data_file(name, before[name])
            raise
    def sync_rpg_runtime(self, files, backup_root):
        allowed = {'RPG/rm0001_dialog.ini', 'RPG/rh_biz_contact.ini', 'SCRIPTS/RPG/conversation.thn'}
        if set(files) != allowed:
            raise ValueError('Unexpected RPG runtime targets')
        for relative in files:
            self.data_path(relative)
        self._sync_rpg_files('rm0001', files, {}, backup_root)
    def sync_rpg_parking_runtime(self, files, backup_root):
        allowed = {'RPG/rm0002_dialog.ini', 'RPG/parking/br_avl_01_base.ini'}
        if set(files) != allowed:
            raise ValueError('Unexpected Avalon parking runtime targets')
        for relative in files:
            self.data_path(relative)
        self._sync_rpg_files('rm0002', files, {}, backup_root)
    # END RPG AUDIO OUTPUT
