import json
g2p=open('tl_g2p.py').read().split('if __name__')[0]
cells=[]
def md(s): cells.append({"cell_type":"markdown","metadata":{},"source":s})
def code(s): cells.append({"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],"source":s})

md("""# 🎙 Tinig — Train free Tagalog voices (male + female)

This notebook trains Tinig's own Tagalog voices on Google Colab's **free GPU**.

* **Data:** the Filipino Speech Corpus (studio-recorded Tagalog, repackaged on Hugging Face as `sapinsapin/filipinospeechcorpus`). The notebook picks the clearest **male** and **female** speakers automatically.
* **Model:** [Piper](https://github.com/OHF-Voice/piper1-gpl) (VITS), warm-started from the public-domain LJSpeech Piper checkpoint so it learns fast.
* **Output:** `tinig-tl.onnx` + `tinig-tl.onnx.json` — send both to Claude to add the voices to Tinig.

### How to run
1. **Runtime → Change runtime type → T4 GPU → Save.**
2. **Runtime → Run all.** Allow Google Drive access when asked (progress is saved there, so you can continue after Colab disconnects).
3. Training runs for hours. If Colab disconnects, just **Run all** again — it continues from the last saved epoch.
4. Anytime you want to hear it, run the **Listen** cell. When it sounds good, run the **Export** cell and download the 2 files.

*Licence note: the corpus repackage is marked MIT for research use and the base checkpoint is public domain. Credit the Filipino Speech Corpus (Sagum) when you publish.*""")

md("## 1 · Settings")
code("""VOICES_PER_GENDER = 2      # 2 → 2 male + 2 female voices in one model
MAX_EPOCHS        = 800    # learning-rate schedule length; you can export earlier
BATCH_SIZE        = 16     # lower to 8 if you get "CUDA out of memory"
WORK = '/content/drive/MyDrive/tinig-voice'   # saved on your Google Drive""")

md("## 2 · Connect Google Drive and check GPU")
code("""from google.colab import drive
drive.mount('/content/drive')
import os, subprocess
os.makedirs(WORK, exist_ok=True)
print(subprocess.run(['nvidia-smi','-L'],capture_output=True,text=True).stdout or '⚠️ No GPU! Runtime → Change runtime type → T4 GPU')""")

md("## 3 · Install Piper training (≈5–8 min)")
code("""%%bash
set -e
apt-get -qq update >/dev/null && apt-get -qq install -y build-essential cmake ninja-build >/dev/null
cd /content
[ -d piper1-gpl ] || git clone -q https://github.com/OHF-voice/piper1-gpl.git
cd piper1-gpl
pip -q install -e '.[train]' 2>&1 | tail -3
pip -q install cython soundfile soxr pyarrow 2>&1 | tail -1
./build_monotonic_align.sh
python3 setup.py build_ext --inplace -q 2>&1 | tail -2
python3 -c "import piper.train.vits.monotonic_align as m; print('✅ Piper training installed')" """)

md("## 4 · Pick speakers and prepare the dataset (≈10–15 min the first time)")
code("""import os, re, io, json, glob, unicodedata, collections
import pyarrow.parquet as pq, numpy as np, soundfile as sf, soxr
from huggingface_hub import snapshot_download

"""+g2p+"""
DATA = os.path.join(WORK,'dataset'); WAVS = os.path.join(DATA,'wavs'); CSV = os.path.join(DATA,'metadata.csv')
if os.path.exists(CSV):
    print('✅ Dataset already prepared on Drive:', sum(1 for _ in open(CSV)), 'clips')
else:
    root = snapshot_download('sapinsapin/filipinospeechcorpus', repo_type='dataset', allow_patterns=['data/*.parquet'], local_dir='/content/fsc')
    files = sorted(glob.glob('/content/fsc/data/*.parquet'))
    cols = ['sentence','duration','num_words','speaker_id','gender','speech_type','source_file']
    bad = re.compile(r'[\\[\\]{}<>()*#@0-9_/=+]')
    rows=[]
    for f in files:
        t = pq.read_table(f, columns=cols).to_pylist()
        for i,r in enumerate(t):
            s=(r['sentence'] or '').strip()
            if r['speech_type']!='read' or not (1.5<=r['duration']<=12) or r['num_words']<3: continue
            if bad.search(s) or len(s)<10: continue
            r['file']=f; r['row']=i; rows.append(r)
    by = collections.defaultdict(float)
    for r in rows: by[(r['gender'], r['speaker_id'])] += r['duration']
    picked=[]
    for g in ('female','male'):
        ranked = sorted([(d,s) for (gg,s),d in by.items() if gg==g], reverse=True)
        print(f'Top {g} speakers (minutes of clean read speech):', [(s, round(d/60,1)) for d,s in ranked[:6]])
        picked += [(g,s) for d,s in ranked[:VOICES_PER_GENDER]]
    names = {}
    for g in ('female','male'):
        for k,(gg,s) in enumerate([p for p in picked if p[0]==g]): names[(gg,s)] = f'{g}_{k+1}'
    print('Using:', names)
    want = collections.defaultdict(dict)
    for r in rows:
        key=(r['gender'],r['speaker_id'])
        if key in names: want[r['file']][r['row']] = (names[key], r['sentence'])
    os.makedirs(WAVS, exist_ok=True); lines=[]; n=0
    for f, idx in want.items():
        t = pq.read_table(f, columns=['audio']).column('audio').to_pylist()
        for i,(spk,sent) in idx.items():
            a = t[i]; data, sr = sf.read(io.BytesIO(a['bytes']), dtype='float32')
            if data.ndim>1: data=data.mean(1)
            data = soxr.resample(data, sr, 22050)
            pk = np.abs(data).max()
            if pk<0.02: continue
            data = data/pk*0.9
            ph = normalize(sent)
            if len(ph)<8: continue
            n+=1; name=f'tinig_{n:05d}.wav'
            sf.write(os.path.join(WAVS,name), data, 22050, subtype='PCM_16')
            lines.append(f'{name}|{spk}|{ph}')
    open(CSV,'w').write('\\n'.join(lines)+'\\n')
    per = collections.Counter(l.split('|')[1] for l in lines)
    print(f'✅ Prepared {len(lines)} clips:', dict(per))
NUM_SPEAKERS = len(set(l.split('|')[1] for l in open(CSV).read().strip().split('\\n')))
print('Speakers:', NUM_SPEAKERS)
print(open(CSV).read().split('\\n')[0])""")

md("## 5 · Train (runs for hours — re-run this cell after a disconnect to continue)")
code("""import glob, os, subprocess
BASE = '/content/lj-med_1000.ckpt'
if not os.path.exists(BASE):
    from huggingface_hub import hf_hub_download
    BASE = hf_hub_download('rhasspy/piper-checkpoints', 'en/en_US/ljspeech/medium/lj-med_1000.ckpt', repo_type='dataset', local_dir='/content')
LOGS = os.path.join(WORK,'logs')
last = sorted(glob.glob(os.path.join(LOGS,'lightning_logs','*','checkpoints','last.ckpt')), key=os.path.getmtime)
cmd = ['python3','-m','piper.train','fit',
  '--data.voice_name','tinig_tl', '--data.csv_path',CSV, '--data.audio_dir',WAVS,
  '--data.phoneme_type','text', '--data.espeak_voice','en-us',
  '--data.cache_dir','/content/cache', '--data.config_path',os.path.join(WORK,'tinig-tl.onnx.json'),
  '--data.batch_size',str(BATCH_SIZE), '--data.num_test_examples','4',
  '--model.sample_rate','22050', '--model.num_speakers',str(NUM_SPEAKERS), '--model.mos_metric','none',
  '--trainer.max_epochs',str(MAX_EPOCHS), '--trainer.default_root_dir',LOGS,
  '--trainer.accelerator','gpu', '--trainer.devices','1', '--trainer.check_val_every_n_epoch','10']
if last:
    print('▶ Continuing from', last[-1]); cmd += ['--ckpt_path', last[-1]]
else:
    print('▶ Starting new training (warm start from LJSpeech)'); cmd += ['--model.warmstart_ckpt', BASE]
p = subprocess.Popen(cmd, cwd='/content/piper1-gpl/src', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
for line in p.stdout:
    if any(k in line for k in ('Epoch','epoch','Error','error','Traceback','Vocoder coverage','speaker','WARNING')): print(line.rstrip()[-300:])
print('Exit code', p.wait())""")

md("## 6 · Listen (run anytime in a second tab or after stopping training)")
code("""import glob, os, subprocess, IPython.display as ipd
TEXT = 'Magandang araw sa inyong lahat. Ito ang bagong boses ni Tinig, at ako ay nagsasalita sa wikang Tagalog.'
ck = sorted(glob.glob(os.path.join(WORK,'logs','lightning_logs','*','checkpoints','last.ckpt')), key=os.path.getmtime)[-1]
subprocess.run(['python3','-m','piper.train.export_onnx','--checkpoint',ck,'--output-file','/content/preview.onnx'], cwd='/content/piper1-gpl/src', check=True)
import onnxruntime as ort, numpy as np, json
cfg = json.load(open(os.path.join(WORK,'tinig-tl.onnx.json'))); idmap = cfg['phoneme_id_map']
ph = list(unicodedata.normalize('NFD', normalize(TEXT)))
ids = idmap['^'] + idmap['_']
for c in ph:
    if c in idmap: ids += idmap[c] + idmap['_']
ids += idmap['$']
sess = ort.InferenceSession('/content/preview.onnx')
for name, sid in cfg.get('speaker_id_map', {'voice':0}).items():
    feeds = {'input':np.array([ids],dtype=np.int64), 'input_lengths':np.array([len(ids)],dtype=np.int64), 'scales':np.array([0.667,1.0,0.8],dtype=np.float32)}
    if cfg.get('num_speakers',1)>1: feeds['sid']=np.array([sid],dtype=np.int64)
    audio = sess.run(None, feeds)[0].squeeze()
    print(name); ipd.display(ipd.Audio(audio, rate=22050))
print('Checkpoint:', ck)""")

md("## 7 · Export for Tinig (download both files and send them to Claude)")
code("""import glob, os, subprocess, shutil
ck = sorted(glob.glob(os.path.join(WORK,'logs','lightning_logs','*','checkpoints','last.ckpt')), key=os.path.getmtime)[-1]
out = os.path.join(WORK,'tinig-tl.onnx')
subprocess.run(['python3','-m','piper.train.export_onnx','--checkpoint',ck,'--output-file',out], cwd='/content/piper1-gpl/src', check=True)
print('✅ Saved to Google Drive → tinig-voice/:', os.path.getsize(out)//1048576, 'MB')
from google.colab import files
files.download(out); files.download(os.path.join(WORK,'tinig-tl.onnx.json'))""")

nb={"cells":cells,"metadata":{"accelerator":"GPU","colab":{"gpuType":"T4","provenance":[]},"kernelspec":{"display_name":"Python 3","name":"python3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":0}
for c in nb['cells']:
    s=c['source']; c['source']=[l+'\n' for l in s.split('\n')]; c['source'][-1]=c['source'][-1].rstrip('\n')
json.dump(nb,open('/home/claude/tinig-tts/train/Tinig_Tagalog_Voice_Training.ipynb','w'),indent=1,ensure_ascii=False)
