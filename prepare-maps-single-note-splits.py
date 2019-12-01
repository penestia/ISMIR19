import os
import fnmatch
import argparse
import re
from collections import defaultdict
import utils


synthnames = set([
    'ENSTDkCl'
])


def desugar(c):
    prefix = 'MAPS_ISOL_NO_'
    last = c[::-1].find('_')
    pid = c[len(prefix):(-last - 1)]

    matches = re.match('([FMP])\_S[01]\_M(\d{1,3})', pid)
    volume = matches.group(1)
    midinote = matches.group(2)

    return pid, volume, midinote


def collect_all_filenames(synthnames):
    filenames = defaultdict(lambda: defaultdict(list))
    for synthname in synthnames:
        for base, dirs, files in os.walk(synthname):
            candidates = fnmatch.filter(files, 'MAPS_ISOL_NO_*.wav')
            if len(candidates) > 0:
                for c in candidates:
                    pid, volume, midinote = desugar(c)
                    path, ext = os.path.splitext(c)
                    filenames[synthname][volume].append((os.path.join(base, path), synthname))
    return filenames


def write_to_file(f, filenames_synthnames):
    for filename, synthname in sorted(filenames_synthnames):
        audiofilename = filename + '.wav'
        midifilename = filename + '.midi'
        instrument = synthname
        f.write('{},{},{}\n'.format(audiofilename, midifilename, instrument))


def main():
    parser = argparse.ArgumentParser('prepare maps splits (+instruments)')
    parser.add_argument('base_dir', help='path to the maps_piano/data folder')
    args = parser.parse_args()

    current_directory = os.getcwd()

    # we change the cwd to 'base_dir', so 'base_dir' is not part
    # of the filename that ends up in the splitfiles
    # we'll change back, once we write the splitfiles
    os.chdir(args.base_dir)

    filenames = collect_all_filenames(synthnames)

    os.chdir(current_directory)
    out_dir = 'splits/maps-isolated-notes'
    utils.ensure_directory_exists(out_dir)
    for synthname, volumes in filenames.items():
        for volume, fns in volumes.items():
            with open(os.path.join(out_dir, '{}_{}'.format(synthname, volume)), 'w') as f:
                write_to_file(f, fns)

    with open(os.path.join(out_dir, 'instruments'), 'w') as f:
        for si, synthname in enumerate(sorted(synthnames)):
            f.write('{},{}\n'.format(synthname, si))


if __name__ == '__main__':
    main()
