import unittest,math
from core import Wing,geometry,polar,performance,naca4
class WingTests(unittest.TestCase):
    def test_rectangular_geometry(self):
        result=geometry(Wing(span_m=2,root_chord_m=0.5,taper=1))
        self.assertEqual(result['area_m2'],1)
        self.assertEqual(result['aspect_ratio'],4)
        self.assertAlmostEqual(result['mac_m'],0.5)
    def test_zero_alpha(self): self.assertEqual(polar(Wing(),0)['lift_n'],0)
    def test_drag_symmetry(self): self.assertEqual(polar(Wing(),5)['cd'],polar(Wing(),-5)['cd'])
    def test_stall_speed_weight(self):
        a=performance(Wing(),2)['estimated_stall_speed_ms']; b=performance(Wing(),4)['estimated_stall_speed_ms']
        self.assertAlmostEqual(b/a,math.sqrt(2))
    def test_symmetric_airfoil(self):
        profile=naca4('0012')
        for u,l in zip(profile['upper'],profile['lower']): self.assertAlmostEqual(u[1],-l[1])
    def test_closed_trailing_edge(self): self.assertAlmostEqual(naca4()['upper'][-1][1],0,places=10)
    def test_invalid_camber(self):
        with self.assertRaises(ValueError): naca4('2012')
    def test_invalid_geometry(self):
        with self.assertRaises(ValueError): geometry(Wing(taper=0))
    def test_feasibility(self): self.assertFalse(performance(Wing(),100,5)['feasible_by_cl_limit'])
