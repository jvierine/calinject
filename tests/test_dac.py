"""Exercise the actual firmware DAC driver with both approved address options."""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'firmware'))
from protocol import MCP4725

class Bus:
    def __init__(self,addresses):self.addresses=addresses;self.writes=[];self.acked=2
    def scan(self):return self.addresses
    def writeto(self,address,data):self.writes.append((address,data));return self.acked

class DacTests(unittest.TestCase):
    def test_both_options_deliver_identical_codes_to_correct_address(self):
        for address in (0x60,0x62):
            b=Bus([0x42,address]);d=MCP4725(b)
            for code in (0,700,1862,3000,4095):
                d.write(code)
                self.assertEqual(b.writes[-1],(address,bytes((code>>8,code&255))))
                self.assertEqual(b.writes[-1][1][0]&0xF0,0) # normal, fast write
    def test_missing_or_ambiguous_dac_fails_before_writes(self):
        for addresses in ([],[0x42],[0x64],[0x60,0x62]):
            b=Bus(addresses)
            with self.assertRaises(ValueError):MCP4725(b)
            self.assertEqual(b.writes,[])
    def test_invalid_codes_cannot_change_output(self):
        b=Bus([0x62]);d=MCP4725(b)
        for code in (-1,4096,1.5,'1862'):
            with self.assertRaises(ValueError):d.write(code)
        self.assertEqual(b.writes,[])
    def test_incomplete_write_is_fault(self):
        b=Bus([0x62]);b.acked=1
        with self.assertRaises(OSError):MCP4725(b).write(1862)

if __name__=='__main__':unittest.main()
