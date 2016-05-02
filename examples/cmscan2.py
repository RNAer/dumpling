
from burrito.parameters import FlagParameter, ValuedParameter
from burrito.util import CommandLineApplication, ResultPath
from tempfile import NamedTemporaryFile
from skbio import write

class CMScan(CommandLineApplication):
    """cmscan application controller.

    INFERNAL 1.1.1 (July 2014)"""
    _command = "cmscan"
    _suppress_stderr = False

    _parameters = { 
        # save parseable table of hits to file
        '--tblout': ValuedParameter('--', Name='tblout', Delimiter=' ', IsPath=True),
        # number of parallel CPU workers to use for multithreads
        '--cpu': ValuedParameter('--', Name='cpu', Delimiter=' ')}
    _synonyms = {'cpu': '--cpu'}
    def _accept_exit_status(self, exit_status):
        return exit_status == 0

    def _get_result_paths(self,data):
        result = {}
        for i in ['--tblout']:
            o = self.Parameters[i]
            if o.isOn():
                out_fp = self._absolute(o.Value)
                result[i] = ResultPath(Path=out_fp, IsWritten=True)
        return result
        
def scan_file(query, db, cpu=1, params=None):
    if params is None:
        params = {}
    params['--cpu'] = cpu
    app = CMScan(InputHandler='_input_as_paths', params=params)
    return app([db, query])

def scan_seq(seq, db, cpu=1, params=None):
    if params is None:
        params = {}
    params['--cpu'] = cpu
    app = CMScan(InputHandler='_input_as_paths', params=params)
    with NamedTemporaryFile(mode='w+') as i:
        write(seq, into=i.name, format='fasta')
        return app([db, i.name])
