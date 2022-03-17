import os
import sys
import numpy as np

from scipy.io import wavfile
from time import *

import torch
import utils
from models import SynthesizerTrn


def save_wav(wav, path, rate):
    wav *= 32767 / max(0.01, np.max(np.abs(wav))) * 0.6
    wavfile.write(path, rate, wav.astype(np.int16))

# define model and load checkpoint
hps = utils.get_hparams_from_file("./configs/singing_base.json")

net_g = SynthesizerTrn(
    hps.data.filter_length // 2 + 1,
    hps.train.segment_size // hps.data.hop_length,
    **hps.model).cuda()

_ = utils.load_checkpoint("./logs/singing_base/G_26000.pth", net_g, None)
net_g.eval()
# net_g.remove_weight_norm()

text_norm = np.load(f"midis/singing_label.npy")
text_tone = np.load(f"midis/singing_pitch.npy")
input_ids = torch.LongTensor(text_norm)
tune_ids = torch.LongTensor(text_tone)

begin_time = time()
with torch.no_grad():
    x_tst = input_ids.cuda().unsqueeze(0)
    x_tst_lengths = torch.LongTensor([input_ids.size(0)]).cuda()
    t_tst = tune_ids.cuda().unsqueeze(0)
    t_tst_lengths = torch.LongTensor([tune_ids.size(0)]).cuda()
    audio = net_g.infer(x_tst, x_tst_lengths, t_tst, t_tst_lengths, noise_scale=0, noise_scale_w=0, length_scale=1)[0][0,0].data.cpu().float().numpy()
end_time = time()
run_time = end_time - begin_time
print('Syth Time (Seconds):', run_time)
data_len = len(audio) / 16000
print('Wave Time (Seconds):', data_len)
print('Real time Rate (%):', run_time/data_len)
save_wav(audio, f"./midis/singing_edit.wav", hps.data.sampling_rate)