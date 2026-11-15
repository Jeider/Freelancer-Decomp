"""Honor deliberately removed port components before flattening their SUR IDs."""
def active_port_hulls(model_root,hulls):
    from station_docks import direct,entries
    import valensia_mega as m
    if direct(model_root,'Cmpnd') is None:return hulls
    names={name for name,_ in entries(model_root)}
    # space_police02 is space_port_dmg with these two compound parts removed.
    # Native collision filters their original IDs. Baking everything as Root
    # would revive the two habitat leaves and the tank leaf.
    absent={m.utf.crc(name) for name in ('junk_hab_lod1','junk_tank_lod1') if name not in names}
    return [h for h in hulls if h.hull_id not in absent]
