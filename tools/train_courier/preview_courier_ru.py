"""Build short listening samples from accepted clean RU source recordings."""
import json
import io
import subprocess
import sys
from pydub import AudioSegment
from generate_courier_ru import OUT, ROOT, ASSETS, sha, save


def base_clip(code):
    sys.path.insert(0,str(ROOT/'tools'))
    from generate_station_lods import read_tree
    game=ASSETS.parent
    result=subprocess.run([str(game/'createid.exe'),'-h','-oc',code],cwd=game,capture_output=True,text=True)
    key=result.stdout.split(',')[1].strip().lower()
    _,roots=read_tree((game/'DATA/AUDIO/dispatcher01.utf').read_bytes())
    def walk(node):
        if node.name.lower()==key:
            return node.blob
        for child in node.children:
            found=walk(child)
            if found is not None:
                return found
    raw=next(raw for node in roots if (raw:=walk(node)) is not None)
    return AudioSegment.from_file(io.BytesIO(raw),format='wav')


def main():
    records = json.loads((OUT/'recordings.json').read_text(encoding='utf-8'))
    choices = {
        'preview_bar': ['rm0001_frag0001_l001_vendor', 'rm0001_frag0026_l001_player', 'rm0001_frag0027_l001_vendor'],
        'preview_space': ['tc_board_01-', 'tc_order_01+', 'gcs_gen_commodity_comm_basic_meds',
                          'tc_destination_01+', 'gcs_refer_base_rh_biz_01_base-', 'tc_collect_01-',
                          'tc_arrival_01-', 'tc_paid_01-', 'te_departed_01-'],
    }
    for name, ids in choices.items():
        combined = AudioSegment.empty()
        order = []
        for code in ids:
            if code.startswith('gcs_refer_base_'):
                segment=base_clip(code).set_frame_rate(24000)
                order.append(dict(id=code,start_seconds=len(combined)/1000,inherited=True))
                combined+=segment
                continue
            record = records[code]
            path = OUT/record['bank']/(code+'.wav')
            assert sha(path)==record['sha256']
            if len(combined):
                previous=order[-1]['id']
                pause=120 if previous.endswith('+') or previous.startswith(('gcs_gen_commodity_','gcs_refer_base_')) else 700
                combined += AudioSegment.silent(duration=pause,frame_rate=24000)
            order.append(dict(id=code,text=record['text'],start_seconds=len(combined)/1000,sha256=record['sha256']))
            combined += AudioSegment.from_wav(path).set_frame_rate(24000)
        target = OUT/(name+'.wav')
        combined.export(target,format='wav')
        save(OUT/(name+'.json'),dict(order=order,sha256=sha(target),seconds=len(combined)/1000,radio_filter=False))
        print(target,round(len(combined)/1000,1),'seconds')


if __name__=='__main__':
    main()
