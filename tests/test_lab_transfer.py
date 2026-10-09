from pathlib import Path
import contextlib,io,json,sys,tempfile,unittest,tarfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import lab_transfer as transfer


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.lab=self.root/'lab';self.lab.mkdir()
        (self.lab/'data').mkdir();(self.lab/'data/array.npy').write_bytes(b'fixture-binary')
        (self.lab/'data/.env').write_text('DO_NOT_TRANSFER=yes')
        (self.lab/'data/config.json').write_text('{"api_key":"do-not-transfer"}')
        (self.lab/'data/opaque.tar.gz').write_bytes(b'opaque')
    def tearDown(self):self.temp.cleanup()
    def inventory(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return transfer.inventory(self.lab,['data'],self.root/'inventory.json')
    def test_exclusions_and_user_selection_roundtrip(self):
        value=self.inventory();self.assertEqual([e['path'] for e in value['files']],['data/array.npy']);self.assertEqual(len(value['excluded']),3)
        (self.root/'selection.json').write_text('["data/array.npy"]')
        with contextlib.redirect_stdout(io.StringIO()):transfer.pack(self.lab,self.root/'inventory.json',self.root/'selection.json',self.root/'export.tar.gz')
        transfer.verify(self.root/'export.tar.gz',self.root/'import',transfer.digest(self.root/'export.tar.gz'))
        self.assertEqual((self.root/'import/data/array.npy').read_bytes(),b'fixture-binary')
        self.assertTrue((self.lab/'data/array.npy').exists())
        with self.assertRaises(ValueError):transfer.verify(self.root/'export.tar.gz',self.root/'import')
    def test_source_change_blocks_pack(self):
        self.inventory();(self.lab/'data/array.npy').write_bytes(b'changed')
        (self.root/'selection.json').write_text('["data/array.npy"]')
        with self.assertRaises(ValueError):transfer.pack(self.lab,self.root/'inventory.json',self.root/'selection.json',self.root/'export.tar.gz')
    def test_path_escape_and_symlink_rejected(self):
        with self.assertRaises(ValueError):transfer.inventory(self.lab,['../outside'],self.root/'i.json')
        (self.lab/'data/link.npy').symlink_to(self.lab/'data/array.npy')
        with self.assertRaises(ValueError):transfer.eligible(self.lab,'data/link.npy')
    def test_wrong_archive_hash_rejected(self):
        p=self.root/'a.gz';p.write_bytes(b'not an archive')
        with self.assertRaises(ValueError):transfer.verify(p,None,'0'*64)
    def test_traversal_archive_rejected_without_output(self):
        p=self.root/'a.gz'
        with tarfile.open(p,'w:gz') as a:
            m=tarfile.TarInfo('../bad');m.size=1;a.addfile(m,io.BytesIO(b'x'))
        with self.assertRaises(ValueError):transfer.verify(p,self.root/'import')
        self.assertFalse((self.root/'import').exists())
    def test_reserved_manifest_path_export_and_import_rejected(self):
        content=b'{"user":"file"}'
        for name in ('LAB_TRANSFER_MANIFEST.json','lab_transfer_manifest.json'):
            (self.lab/name).write_bytes(content)
            with self.assertRaises(ValueError):transfer.eligible(self.lab,name)
        archive=self.root/'collision.tar.gz'
        manifest={'schema':1,'files':[{'path':'LAB_TRANSFER_MANIFEST.json','bytes':len(content),
                                     'sha256':transfer.hashlib.sha256(content).hexdigest()}]}
        with tarfile.open(archive,'w:gz') as a:
            for name,data in [('LAB_TRANSFER_MANIFEST.json',json.dumps(manifest).encode()),
                              ('files/LAB_TRANSFER_MANIFEST.json',content)]:
                m=tarfile.TarInfo(name);m.size=len(data);a.addfile(m,io.BytesIO(data))
        with self.assertRaises(ValueError):transfer.verify(archive,self.root/'import')
        self.assertFalse((self.root/'import').exists())


if __name__=='__main__':unittest.main()
