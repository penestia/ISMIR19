import os
import fnmatch
import argparse
import utils



test_synthnames = set([
    'ENSTDkCl',
    'ENSTDkAm'
])

train_synthnames = set([
    'StbgTGd2',
    'SptkBGCl'
])

def desugar(c):
    prefix = 'MIDI'
    last = c[::-1].find('_')
    pid = c[len(prefix):(-last - 1)]
    return prefix, last, pid


def collect_all_piece_ids(synthnames):
    pids = set()
    for synthname in synthnames:
        for base, dirs, files in os.walk(synthname):
            candidates = fnmatch.filter(files, '*Unprocessed*.wav')
            if len(candidates) > 0:
                for c in candidates:
                    _, _, pid = desugar(c)
                    pids.add(pid)

    return pids


def collect_all_filenames(synthnames, include):
    filenames = []
    for synthname in synthnames:
        for base, dirs, files in os.walk(synthname):
            candidates = fnmatch.filter(files, '*Unprocessed*.wav')
            if len(candidates) > 0:
                for c in candidates:
                    _, _, pid = desugar(c)
                    if pid in include:
                        path, ext = os.path.splitext(c)
                        filenames.append((os.path.join(base, path), synthname))
    return filenames


def write_to_file(f, filenames_synthnames):
    for filename, synthname in sorted(filenames_synthnames):
        audiofilename = filename + '.wav'
        midifilename = filename + '.midi'
        instrument = synthname
        f.write('{},{},{}\n'.format(audiofilename, midifilename, instrument))


def main():
    parser = argparse.ArgumentParser('prepare maestro splits (+instruments)')
    parser.add_argument('base_dir', help='path to the maestro folder')
    args = parser.parse_args()

    current_directory = os.getcwd()

    # we change the cwd to 'base_dir', so 'base_dir' is not part
    # of the filename that ends up in the splitfiles
    # we'll change back, once we write the splitfiles
    os.chdir(args.base_dir)

    train_pids = collect_all_piece_ids(train_synthnames)
    test_pids = collect_all_piece_ids(test_synthnames)

    print('len(train_pids)', len(train_pids))
    print('len(test_pids)', len(test_pids))

    train_filenames = collect_all_filenames(train_synthnames, train_pids - test_pids)
    test_filenames = collect_all_filenames(test_synthnames, test_pids)

    # this just selects the first from each synth as a 'validation' set
    valid_filenames = []
    for synthname_a in sorted(train_synthnames):
        for filename, synthname_b in sorted(train_filenames):
            if synthname_a == synthname_b:
                valid_filenames.append((filename, synthname_a))
                break

    print('len(train_filenames)', len(train_filenames))
    print('len(valid_filenames)', len(valid_filenames))
    print('len(test_filenames)', len(test_filenames))

    os.chdir(current_directory)

    out_dir = 'splits/maestro-non-overlapping'
    utils.ensure_directory_exists(out_dir)

    with open(os.path.join(out_dir, 'train'), 'w') as f:
        write_to_file(f, train_filenames)

    with open(os.path.join(out_dir, 'valid'), 'w') as f:
        write_to_file(f, valid_filenames)

    with open(os.path.join(out_dir, 'test'), 'w') as f:
        write_to_file(f, test_filenames)

    with open(os.path.join(out_dir, 'instruments'), 'w') as f:
        all_synthnames = train_synthnames | test_synthnames
        for si, synthname in enumerate(sorted(all_synthnames)):
            f.write('{},{}\n'.format(synthname, si))


if __name__ == '__main__':
    main()
