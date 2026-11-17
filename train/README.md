# Train Tinig's Tagalog voices

Open the notebook in Google Colab (free GPU):

https://colab.research.google.com/github/ajcajandab-png/tinig-tts/blob/main/train/Tinig_Tagalog_Voice_Training.ipynb

- Data: Filipino Speech Corpus (Sagum), via `sapinsapin/filipinospeechcorpus` on Hugging Face.
- Model: Piper (VITS), warm-started from the public-domain LJSpeech medium checkpoint.
- Output: `tinig-tl.onnx` + `tinig-tl.onnx.json` → put both in `/voices` and the site picks them up automatically.

`tl_g2p.py` (training) and `../tl-g2p.js` (website) must stay identical in behaviour.
