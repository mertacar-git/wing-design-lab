"""Transparent low-speed finite-wing estimates and NACA four-digit geometry."""
from dataclasses import dataclass,asdict
import math

@dataclass(frozen=True)
class Wing:
    span_m: float = 2.0
    root_chord_m: float = 0.35
    taper: float = 0.6
    sweep_deg: float = 0.0
    efficiency: float = 0.8
    cd0: float = 0.025
    cl_max: float = 1.2

    def validate(self):
        if not all(math.isfinite(v) for v in asdict(self).values()): raise ValueError('Wing parameters must be finite.')
        if not 0.1 <= self.span_m <= 100 or not 0.01 <= self.root_chord_m <= 20 or not 0.1 <= self.taper <= 1:
            raise ValueError('Invalid span, root chord or taper.')
        if not -30 <= self.sweep_deg <= 45 or not 0.1 <= self.efficiency <= 1 or not 0 <= self.cd0 <= 0.5 or not 0.1 <= self.cl_max <= 3:
            raise ValueError('Invalid aerodynamic inputs.')

def geometry(wing):
    wing.validate()
    tip=wing.root_chord_m*wing.taper
    area=wing.span_m*(wing.root_chord_m+tip)/2
    mac=2*wing.root_chord_m/3*(1+wing.taper+wing.taper**2)/(1+wing.taper)
    return dict(area_m2=area,aspect_ratio=wing.span_m**2/area,tip_chord_m=tip,mac_m=mac)

def polar(wing,alpha_deg,speed_ms=20,density=1.225,alpha_zero_deg=0):
    values=[alpha_deg,speed_ms,density,alpha_zero_deg]
    if not all(math.isfinite(v) for v in values) or not 0 < speed_ms <= 100 or not 0 < density <= 2 or not -20 <= alpha_deg <= 20:
        raise ValueError('Use finite inputs, positive speed (up to 100 m/s), density (up to 2 kg/m³) and alpha within ±20°.')
    g=geometry(wing)
    a0=2*math.pi*math.cos(math.radians(wing.sweep_deg))
    slope=a0/(1+a0/(math.pi*wing.efficiency*g['aspect_ratio']))
    cl=slope*math.radians(alpha_deg-alpha_zero_deg)
    cdi=cl**2/(math.pi*wing.efficiency*g['aspect_ratio'])
    cd=wing.cd0+cdi
    q=0.5*density*speed_ms**2
    return dict(alpha_deg=alpha_deg,cl=cl,cd=cd,cdi=cdi,lift_n=q*g['area_m2']*cl,
                drag_n=q*g['area_m2']*cd,lift_drag=cl/cd if cd else None,
                beyond_cl_max=abs(cl)>wing.cl_max,lift_slope_per_rad=slope)

def performance(wing,mass_kg=2,speed_ms=20,density=1.225):
    if not math.isfinite(mass_kg) or not 0 < mass_kg <= 10000: raise ValueError('Mass must be positive and finite.')
    reference=polar(wing,0,speed_ms,density)
    g=geometry(wing)
    cl=mass_kg*9.80665/(0.5*density*speed_ms**2*g['area_m2'])
    alpha=math.degrees(cl/reference['lift_slope_per_rad'])
    return dict(**g,required_cl=cl,required_alpha_deg=alpha,
                estimated_stall_speed_ms=math.sqrt(2*mass_kg*9.80665/(density*g['area_m2']*wing.cl_max)),
                feasible_by_cl_limit=cl<=wing.cl_max)

def planform(wing):
    g=geometry(wing); half=wing.span_m/2
    offset=math.tan(math.radians(wing.sweep_deg))*half
    return [(0,0),(half,offset),(half,offset+g['tip_chord_m']),(0,wing.root_chord_m),(-half,offset+g['tip_chord_m']),(-half,offset),(0,0)]

def naca4(code='2412',points=81):
    if len(code)!=4 or not code.isdigit() or not 11 <= points <= 501: raise ValueError('Use four NACA digits and 11–501 points.')
    m=int(code[0])/100; p=int(code[1])/10; thickness=int(code[2:])/100
    if not 0 < thickness <= 0.4 or (m>0 and p==0): raise ValueError('Invalid NACA camber position or thickness.')
    upper=[]; lower=[]
    for i in range(points):
        x=(1-math.cos(math.pi*i/(points-1)))/2
        yt=5*thickness*(0.2969*math.sqrt(x)-0.1260*x-0.3516*x*x+0.2843*x**3-0.1036*x**4)
        if m==0: yc=slope=0
        elif x<p: yc=m/p**2*(2*p*x-x*x); slope=2*m/p**2*(p-x)
        else: yc=m/(1-p)**2*((1-2*p)+2*p*x-x*x); slope=2*m/(1-p)**2*(p-x)
        angle=math.atan(slope)
        upper.append((x-yt*math.sin(angle),yc+yt*math.cos(angle)))
        lower.append((x+yt*math.sin(angle),yc-yt*math.cos(angle)))
    return dict(upper=upper,lower=lower)
