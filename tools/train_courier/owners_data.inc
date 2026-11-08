    def sync_courier_owners(self, files, backup_root):
        """Publish locomotive contacts, catalog and required transfer registrations."""
        import re
        allowed = {'RPG/courier_contacts.ini', 'RPG/rh_biz_contact.ini',
                   'MISSIONS/TrainCourier/catalog.ini', 'UNIVERSE/universe.ini', 'MISSIONS/mbases.ini'}
        for name in files:
            if (name not in allowed and
                    not re.fullmatch(r'UNIVERSE/TrainCourier/tc_[a-z0-9_]+_base\.ini', name) and
                    not re.fullmatch(r'MISSIONS/TrainCourier/launch_[a-z0-9_]+\.ini', name) and
                    not re.fullmatch(r'RPG/courier/[a-z0-9_]+_base(?:_dialog)?\.ini', name) and
                    not re.fullmatch(r'SCRIPTS/RPG/rm[0-9]{4}/(?:conversation\.thn|gestures/(?:vendor|player)_0[1-8]\.thn)', name)):
                raise ValueError('Unexpected courier owner target: ' + name)
            self.data_path(name)
        self._sync_rpg_files('courier_owners', files, {}, backup_root)

