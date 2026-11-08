    def sync_parking_ui(self, files, backup_root):
        """Publish the parking button and presentation-only RPG contact icon edits."""
        import re
        allowed = {'Interface/Baseside/navbar.ini', 'Interface/Baseside/parking_p.3db',
                   'RPG/rh_biz_contact.ini'}
        for name in files:
            if name not in allowed and not re.fullmatch(r'RPG/(?:parking|courier)/[a-z0-9_]+\.ini', name):
                raise ValueError('Unexpected parking UI target: ' + name)
            self.data_path(name)
            if name.startswith('RPG/'):
                original = self.data_path(name).read_bytes()
                content = files[name]
                # Changing the marker must never rewrite the actor or dialogue.
                strip = lambda data: re.sub(rb'(?im)^icon\s*=[^\r\n]*\r?\n', b'', data)
                if strip(original) != strip(content):
                    raise ValueError('Contact edit is not icon-only: ' + name)
                icons = re.findall(rb'(?im)^icon\s*=\s*(mission|rumor)\s*$', content)
                if len(icons) != 1:
                    raise ValueError('Expected one valid contact icon: ' + name)
        self._sync_rpg_files('parking_ui', files, {}, backup_root)

