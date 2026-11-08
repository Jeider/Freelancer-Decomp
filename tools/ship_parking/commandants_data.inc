    def sync_parking_commandants(self, files, backup_root):
        """Atomic commandants, additive parking hotspots and missing base definitions."""
        import re
        allowed = {'RPG/ship_parking.ini', 'RPG/parking_contacts.ini',
                   'Interface/Baseside/navbar.ini', 'Interface/Baseside/parking_p.3db',
                   'Universe/SYSTEMS_MOD/CO_MADRID/co_mad_04_base.ini',
                   'Universe/DANGEON/ARCH/arch_01_base.ini',
                   'Universe/DANGEON/HEAVY_BARREL2/heavy_barrel2_01_base.ini'}
        for name in files:
            # Room edits are constrained to the additive parking-hotspot transform.
            room = name.lower().startswith('universe/') and name.lower().endswith('.ini') and name not in allowed
            if room:
                from managers.parking_rooms import ensure_parking_hotspot, LANDING_PATHS
                from managers.parking_commandants import parse, one
                content = files[name]
                if isinstance(content, str): content = content.encode('utf-8')
                declared_dealer = name.lower() in LANDING_PATHS
                if not declared_dealer and not any(k == 'hotspot' and one(r, 'behavior').lower() == 'startshipdealer'
                           for k, r in parse(content)):
                    raise ValueError('Room is not a ship dealer: ' + name)
                if ensure_parking_hotspot(content, declared_dealer) != content:
                    raise ValueError('Missing parking hotspot: ' + name)
                target = self.data_path(name)
                if target.exists() and ensure_parking_hotspot(target.read_bytes(), declared_dealer) != content:
                    raise ValueError('Room changed since planning or edit is not additive: ' + name)
                continue
            if (name not in allowed and
                    not re.fullmatch(r'RPG/parking/[a-z0-9_]+_base\.ini', name) and
                    not re.fullmatch(r'RPG/rm[0-9]{4}_dialog\.ini', name) and
                    not re.fullmatch(r'SCRIPTS/RPG/rm[0-9]{4}/conversation\.thn', name)):
                raise ValueError('Unexpected parking commandant target: ' + name)
            self.data_path(name)
        self._sync_rpg_files('parking_commandants', files, {}, backup_root)

