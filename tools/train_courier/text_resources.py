"""Stable courier string IDs; compilation is explicit in the staging workflow."""
from pathlib import Path
import shutil
import subprocess
import sys
import ast

# Append entries only: installed saves/configs retain the first six IDs.
IDS_KEYS=['title','board','pickup','deliver','park','continue','launch','recover']
TEXTS={
    'ru':['Диспетчер грузовых перевозок','Совершите стыковку с локомотивом.',
          'Подцепите назначенный состав.','Привезите груз к точке %s0 и отцепите состав.',
          'Припаркуйте локомотив у стыковочного узла планеты %s0.','Доставка оплачена. Продолжить работу?',
          'Вылетите в космос.','Груз отцеплен. Подцепите его обратно.'],
    'en':['Freight dispatcher','Dock with the locomotive.',
          'Couple the assigned wagons.','Deliver the cargo to %s0 and uncouple the train.',
          'Park the locomotive at the docking fixture of planet %s0.','Delivery paid. Continue working?',
          'Launch into space.','Cargo detached. Couple the wagons again.'],
}

RESOURCE_KEYS=IDS_KEYS+['offer','accept','accept_10','accept_20','decline']
TEXT_IDS={key:238270+i for i,key in enumerate(RESOURCE_KEYS)}
TEXTS['ru'] += ['Есть работа для машиниста. Выберите начальный состав; каждый рейс оплачивается отдельно.',
                'Берусь: 2 вагона.', 'Берусь: 10 вагонов.', 'Берусь: 20 вагонов.', 'Не сейчас.']
TEXTS['en'] += ['We need a train driver. Choose your starting train; each delivery is paid separately.',
                'Start with 2 wagons.', 'Start with 10 wagons.', 'Start with 20 wagons.', 'Not now.']

from order_texts import rows as order_rows
for key,number,ru,en in order_rows():
    RESOURCE_KEYS.append(key);TEXT_IDS[key]=number
    TEXTS['ru'].append(ru);TEXTS['en'].append(en)


def vendor_dialog():
    text=f'[Dialog]\nstart = tc_offer\n\n[DialogNode]\nnickname = tc_offer\ntext_ids = {TEXT_IDS["offer"]}\n'
    for key,count in [('accept',2),('accept_10',10),('accept_20',20),('decline',None)]:
        text+=f'\n[DialogChoice]\nnode = tc_offer\ntext_ids = {TEXT_IDS[key]}\n'
        text+=f'action = start_train_courier\nfirst_wagons = {count}\n' if count else 'action = close\n'
    return text


def localized_rows(game,static_path=None):
    path=static_path or game/'Assets/Pythonlancer/text/static.py'
    tree=ast.parse(path.read_text(encoding='utf-8'))
    registered={n.args[0].value:n.args[1] for n in ast.walk(tree)
                if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Static'
                and len(n.args)==2 and isinstance(n.args[0],ast.Constant)}
    rows=[]
    for i,key in enumerate(RESOURCE_KEYS):
        number=TEXT_IDS[key]
        value=registered.get(number)
        if value is None:ru,en=TEXTS['ru'][i],TEXTS['en'][i]
        else:
            assert isinstance(value,ast.Call) and isinstance(value.func,ast.Name) and value.func.id=='MS'
            ru,en=[ast.literal_eval(arg) for arg in value.args]
        rows.append((number,ru,en))
    return rows,registered


def stage_localized(game,out,put,static_path=None):
    """Use Pythonlancer static translations and preserve all unrelated resources."""
    root=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(root/'tools/targeting_hud'))
    import stage_interface_strings as ids
    from export import sections
    from launchers import startup_inis
    rows,registered=localized_rows(game,static_path)
    relative='Assets/Pythonlancer/text/static.py'
    original=(static_path or game/relative).read_text(encoding='utf-8')
    extra=''.join(f'    Static({number}, MS({ru!r}, {en!r})),  # TrainCourier {key}\n'
                  for key,(number,ru,en) in zip(RESOURCE_KEYS,rows) if number not in registered)
    if extra:
        assert 'STATIC_NAMES = [\n' in original
        patched=original.replace('STATIC_NAMES = [\n','STATIC_NAMES = [\n'+extra,1)
        ast.parse(patched);put(relative,patched)
    for ini in startup_inis(game):
        resource=next(s for k,s in sections(ini) if k=='resources')['dll'][2]
        actual=(game/'bin'/resource.replace('\\','/')).resolve()
        english='resources_eng' in str(actual).lower()
        assert actual.name.lower()=='nameresources.dll' and actual.is_relative_to(game.resolve())
        relative=actual.relative_to(game.resolve()).as_posix()
        before=ids.resources(actual);expected=dict(before);blocks={}
        for number,ru,en in rows:
            block,slot=(number&65535)//16+1,number%16
            keys=[k for k in before if k[0]==6 and k[1]==block] or [(6,block,1033)]
            for k in keys:
                strings=blocks.setdefault(k,ids.decode_block(before.get(k,b'\0'*32)))
                # The static cache is authoritative on subsequent edits.
                assert number in registered or not strings[slot], f'Occupied unregistered IDS {number}: {strings[slot]}'
                strings[slot]=en if english else ru
        temp=out/('courier_names_en.dll' if english else 'courier_names_ru.dll')
        shutil.copy2(actual,temp)
        h=ids.check(ids.begin(str(temp),False))
        try:
            for (kind,block,lang),strings in blocks.items():
                raw=ids.encode_block(strings);buf=ids.c.create_string_buffer(raw)
                ids.check(ids.update(h,kind,block,lang,buf,len(raw)));expected[kind,block,lang]=raw
        except Exception:
            ids.end(h,True);raise
        ids.check(ids.end(h,False))
        assert ids.resources(temp)==expected,'Unrelated resource changed'
        put(relative,temp.read_bytes())
    return rows

def build(out,language):
    root=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(root/'tools/nebula_control'))
    from build_asf_hq import compiler_env
    compiler,env=compiler_env()
    rc=shutil.which('rc.exe',path=env['PATH']);assert rc,'Windows SDK rc.exe unavailable'
    for lang,lines in TEXTS.items():
        # Legacy appended DLL remains available for old save-game objectives.
        path=out/('text_'+lang+'.rc')
        escaped=[text.replace('\\','\\\\').replace('"','""').replace('\n','\\n') for text in lines]
        path.write_text('#include <windows.h>\nSTRINGTABLE\nBEGIN\n'+
                        ''.join(f'{i} "{text}"\n' for i,text in enumerate(escaped,1))+'END\n',encoding='utf-16')
        res=out/('text_'+lang+'.res');dll=out/('text_'+lang+'.dll')
        subprocess.run([rc,'/nologo','/fo',str(res),str(path)],env=env,check=True,capture_output=True)
        subprocess.run([str(compiler/'link.exe'),'/nologo','/dll','/noentry','/machine:x86',
                        '/out:'+str(dll),str(res)],env=env,check=True,capture_output=True)
    return (out/('text_'+language+'.dll')).read_bytes()
