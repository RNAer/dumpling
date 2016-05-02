
from tempfile import NamedTemporaryFile
from skbio import write
from dumpling import check_choice, Dumpling, OptionParam, ArgmntParam, Parameters


_params = [
        OptionParam('--tblout', name='out', help='save parseable table of hits to file'),
        OptionParam('--cpu', value=1, help='number of parallel CPU workers to use for multithreads'),
        ArgmntParam(name='db', help='HMM/CM database file'),
        ArgmntParam(name='query', help='input sequence to scan')]

def scan_file(query, db, cpu=1, **kwargs):
    cmscan = Dumpling('cmscan', params=Parameters(*_params))
    cmscan.update(query=query, db=db, **kwargs)
    return cmscan()

def scan_seq(seq, db, cpu=1, **kwargs):
    cmscan = Dumpling('cmscan', params=Parameters(*_params))
    with NamedTemporaryFile(mode='w+') as i:
        write(seq, into=i.name, format='fasta')
        cmscan.update(query=i.name, db=db, **kwargs)
        return cmscan()
