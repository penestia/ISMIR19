# ISMIR19
This is code to reproduce the results in [this paper](http://arxiv.org/abs/1909.01622).

## Installation

it is recommended you first create a python 3 virtual environment

```
$ python3 -m venv ISMIR19
$ cd ISMIR19
$ source bin/activate
$ git https://github.com/penestia/ISMIR19.git
```

until a new madmom version is released on pip, you'll have to build madmom from source:

```
$ pip install -r ISMIR19/requirements_00.txt
$ git clone https://github.com/CPJKU/madmom.git
$ cd madmom
$ git submodule update --init --remote
$ python setup.py develop
$ cd ..
```

you should have madmom version 0.17.dev0 or higher now (you can check with `pip list` what is installed where, and if it's indeed a `develop` install that points to your virtualenv)

now we'll install the second set of requirements

```
$ pip install -r ISMIR19/requirements_01.txt
```

## Data
While the original work uses MAESTRO dataset, we use MAESTRO dataset, and you can find this dataset here https://magenta.tensorflow.org/datasets/maestro. Make sure you get the full dataset that holds both the wav and midi files.
create datadirectory, 
```
$ mkdir data
$ cd data
$ ln -s <path-to-where-MAESTRO-was-extracted-to> .
$ cd ..
```

create metadata-file for non-overlapping MAESTRO subset (or use the ones checked in ...)
```
$ python prepare-maestro-non-overlapping-splits.py data/maestro_piano/data
```


create metadata-file for MAESTRO subset as isolated tracks (or use the ones checked in ...)
```
$ python prepare-maestro-individual-tracks.py data/maestro_piano/data
```

## Training
train a model on MAESTRO (the script automatically uses CUDA, if pytorch knows about it)
```
$ python train.py
```

## Generating all the plots
(you will need a (trained) model file for this)

##### Figures 1 and 5
- this generates figure 1 (among other, similar figures) by going from [x, x_pad] -> [y, yz_pad, z] and back again
- filename for figure 1 is `z_hat_pad_y_hat_input_output_MAESTRO_MUS-chpn-p19_ENSTDkCl.pdf`
- this also generates figure 5 (among other, similar figures) by replacing the inferred [y, yz_pad, z] vector by something produced by an oracle (a perfectly working denoising algorithm, for example, or the groundtruth)
- this is to see what happens when we use the network as a conditional GAN only
- filename for figure 5 is `z_samp_zero_y_true_input_output_MAPS_MUS-chpn-p19_ENSTDkCl.pdf`

```
$ python plot_maestro_spec2labels_xyz.py runs/<run-name>/model_state_final.pkl plots/xyz
```

##### Figure 4
- this generates figure 4 (among other, similar figures) by going from [x, x_pad] -> [y, yz_pad, z] -> [y_denoised, 0, z ~ N(O,I)] -> [x_sampled, x_pad_sampled]
- the 'editing' of the inferred variables in y_denoised is done in a **very ad-hoc** fashion, nowhere near a proper denoising algorithm ...
- filename `z_zero_y_edit_input_output_MAPS_MUS-chpn-p19_ENSTDkCl.pdf`

```
$ python plot_maestro_spec2labels_edit_xyz.py runs/<run-name>/model_state_final.pkl plots/edit_xyz
```


## Demo GUI (to edit latent codes and have direct feedback)

- the demo GUI ended up in a different [repository](https://github.com/rainerkelz/ISMIR19-GUI).

## Training the key-wise RNNs on the latent codes from a trained INN model

- prerequisites: a trained invertible model (the GUI repo contains a pre-trained model, if you want to skip the training step)
- we need to export the latent codes that the model produces from the data
```
$ mkdir exports
$ python export_maestro_spec2labels.py runs/<run-name>/model_state_final.pkl exports/<run-name>
```

- train the key-wise RNNs
```
$ python train_rnn_gru.py exports/<run-name>
$ python train_rnn_lstm.py exports/<run-name>
$ python train_rnn_gru_larger.py exports/<run-name>
```

- test the key-wise RNNs
```
$ python test_rnn_gru.py runs/rnn_gru_maestro_spec2labels_swd/model_state_best.pkl exports/<run-name>
$ python test_rnn_lstm.py runs/rnn_lstm_maestro_spec2labels_swd/model_state_best.pkl exports/<run-name>
$ python test_rnn_gru_larger.py runs/rnn_gru_larger_maestro_spec2labels_swd/model_state_best.pkl exports/<run-name>
```
- if you use the pretrained model in this [repository](https://github.com/rainerkelz/ISMIR19-GUI) for exporting, and let the different RNNs train for a while (~a day or two), they should achieve approximately these results:

Type  | F-measure (framewise)
------|------------------------
GRU   | 0.7137
LSTM  | 0.7125
biGRU | 0.7393

- this makes them about as useful as a CNN with 5 frames of context, for piano transcription

## FAQ

### Question
> You included "note phase" in the output features,
> and defined it in the range of [0,5]. But it doesn't look like
> to be a "real" phase, but something more like note loudness?

### Answer
Yes, "note phase" means phase in the following sense: "a distinct period or stage in a series of events or a process of change or development" and describes the current temporal evolution of the note. It is **not** supposed to describe overall loudness. That is what the velocity outputs are there for.

- "velocity" corresponds roughly to loudness
- "note phase" corresponds roughly to positional encoding of the temporal evolution of the spectrum


### Question
> Is there any special considerations why you decided to define a
> different range for the "note phase" rather than [0,1]?

### Answer
Yes, it is a last minute hack to get a more useful error signal... one could do this in any number of other ways though.


### Question
> It looks you are designing the model in a multitask manner, have
> you tried other simpler output encodings (something more close to the
> baselines in your experiment)?

### Answer
That is definitely possible, but there are some caveats. We're assuming you mean
something along the lines of "map a spectrogram frame to a binary indicator vector",
ignoring all temporal aspects of notes.

This would definitely "work", but the results of using the model in the
generative direction would be very different. Assume you are setting
some note to "1" in the latent space and then generate. This would then
yield an **arbitrary** sample of a spectrogram frame corresponding to the
note. You could not specify that you wanted an onset frame or somewhere
in the middle anymore!

One could certainly fix that, by using recurrent invertible models for example.
These are relatively easy to write down on paper, yet surprisingly difficult
to tame practically. (At least we found them to be that way ...)
